from datetime import datetime, timezone

from db import SessionLocal
from models import ProcessedData, RawData
from sqlalchemy.orm import Session

from .base import BaseAgent


class DataEngineerAgent(BaseAgent):
    def __init__(self):
        super().__init__(name="DataEngineer")

    def process_raw_data(self, raw_id: int):
        db: Session = SessionLocal()

        try:
            raw_entry = db.query(RawData).filter(RawData.id == raw_id).first()
            if not raw_entry:
                self.log(
                    "process_raw_data",
                    {"error": "raw_data not found", "raw_id": raw_id},
                )
                return None

            # Basic cleaning/processing
            structured = {
                "text_length": len(str(raw_entry.content)),
                "raw_content": raw_entry.content,
                "processed_at": datetime.now(timezone.utc).isoformat(),
            }

            processed_entry = ProcessedData(structured=structured)
            db.add(processed_entry)
            db.commit()
            db.refresh(processed_entry)

            self.log(
                "process_raw_data",
                {"raw_id": raw_id, "processed_id": processed_entry.id},
            )

            return processed_entry.id

        finally:
            db.close()
