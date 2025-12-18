from datetime import datetime, timezone

from db import SessionLocal
from models import ProcessedData, Report, Violation
from sqlalchemy import Integer, cast, text
from sqlalchemy.orm import Session

from .base import BaseAgent


class ReportWriterAgent(BaseAgent):
    def __init__(self):
        super().__init__(name="ReportWriter")

    def generate_report(self, report_id: int):
        db: Session = SessionLocal()

        try:
            report = db.query(Report).filter(Report.id == report_id).first()
            if not report:
                self.log(
                    "generate_report",
                    {"error": "report not found", "report_id": report_id},
                )
                return None

            processed_id = report.content.get("processed_id")

            processed = (
                db.query(ProcessedData).filter(ProcessedData.id == processed_id).first()
            )

            violations = (
                db.query(Violation)
                .filter(
                    cast(text("violations.details ->> 'processed_id'"), Integer)
                    == processed_id
                )
                .all()
            )

            structured_report = {
                "meta": {
                    "generated_at": datetime.now(timezone.utc).isoformat(),
                    "report_id": report.id,
                    "processed_id": processed_id,
                },
                "summary": report.summary,
                "risk_score": report.score,
                "violations": [
                    {
                        "rule": v.rule,
                        "severity": v.severity,
                        "details": v.details,
                    }
                    for v in violations
                ],
                "data_snapshot": processed.structured if processed else {},
            }

            report.content = structured_report
            db.commit()

            self.log(
                "generated_report",
                {
                    "report_id": report.id,
                    "num_violations": len(violations),
                    "risk_score": report.score,
                },
            )

            return structured_report
        finally:
            db.close()
