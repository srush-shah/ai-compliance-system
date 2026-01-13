import csv
import json
from io import StringIO
from typing import cast

from adk.tools.tools_registry import get_adk_tools
from db import SessionLocal
from fastapi import APIRouter, BackgroundTasks, Depends, File, UploadFile
from models import RawData
from services.compliance_runner import run_compliance_workflow
from sqlalchemy.orm import Session

router = APIRouter(prefix="/upload", tags=["upload"])
tools = get_adk_tools()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@router.post("")
async def upload_file(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
):
    content = await file.read()
    file_name = file.filename
    content_type = file.content_type or ""
    decoded = content.decode(errors="ignore")

    parsed: dict[str, object] = {
        "raw_text": decoded,
        "file_name": file_name,
        "file_type": "text",
        "source": "upload",
    }

    if (file_name and file_name.lower().endswith(".csv")) or "csv" in content_type:
        try:
            reader = csv.DictReader(StringIO(decoded))
            rows = [row for row in reader]
            parsed["file_type"] = "csv"
            parsed["csv_rows"] = rows
        except Exception:
            parsed["file_type"] = "text"
    else:
        try:
            parsed_json = json.loads(decoded)
            parsed["file_type"] = "json"
            parsed["parsed_json"] = parsed_json
        except Exception:
            parsed["file_type"] = "text"

    record = RawData(
        content=parsed,
        file_name=file_name,
        file_type=parsed.get("file_type"),
        source="upload",
    )
    db.add(record)
    db.commit()
    db.refresh(record)

    # After commit/refresh, SQLAlchemy will have populated the integer primary key.
    raw_id = cast(int, record.id)

    # Create an ADK run for this raw record, then start the workflow in the background
    adk_run = tools["create_adk_run"](raw_id=raw_id, status="started")

    background_tasks.add_task(
        run_compliance_workflow,
        raw_id,
        adk_run["id"],
        False,
    )

    return {
        "status": "stored",
        "raw_data_id": record.id,
        "run_id": adk_run["id"],
        "workflow_started": True,
    }
