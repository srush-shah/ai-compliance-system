import json
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

    try:
        parsed = json.loads(content)
    except Exception:
        parsed = {"raw_text": content.decode(errors="ignore")}

    record = RawData(content=parsed)
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
