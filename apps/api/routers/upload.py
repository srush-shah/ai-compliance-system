import json

from db import SessionLocal
from fastapi import APIRouter, Depends, File, UploadFile
from models import RawData
from sqlalchemy.orm import Session

router = APIRouter(prefix="/upload", tags=["upload"])


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@router.post("")
async def upload_file(file: UploadFile = File(...), db: Session = Depends(get_db)):
    content = await file.read()

    try:
        parsed = json.loads(content)
    except Exception:
        parsed = {"raw_text": content.decode(errors="ignore")}

    record = RawData(content=parsed)
    db.add(record)
    db.commit()
    db.refresh(record)

    return {"status": "stored", "raw_data_id": record.id}
