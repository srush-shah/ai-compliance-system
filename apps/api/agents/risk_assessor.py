from datetime import datetime, timezone

from db import SessionLocal
from models import ProcessedData, Report, Violation
from sqlalchemy import Integer, cast, text
from sqlalchemy.orm import Session

from .base import BaseAgent


class RiskAssessorAgent(BaseAgent):
    def __init__(self):
        super().__init__(name="RiskAssessor")

    def assess_risk(self, processed_id: int):
        db: Session = SessionLocal()
        try:
            processed_entry = (
                db.query(ProcessedData).filter(ProcessedData.id == processed_id).first()
            )
            if not processed_entry:
                self.log(
                    "assess_risk",
                    {"error": "processed_data not found", "processed_id": processed_id},
                )
                return None

            # Fetch violations
            # Use PostgreSQL's ->> operator to extract JSON as text, then cast to Integer
            violations = (
                db.query(Violation)
                .filter(
                    cast(
                        text("violations.details ->> 'processed_id'"),
                        Integer,
                    )
                    == processed_id
                )
                .all()
            )

            # Simple risk scoring: 1 violation = 10 points, max 100
            risk_score = min(len(violations) * 10, 100)

            # Optional: create a summary report entry
            report = Report(
                summary=f"Processed ID {processed_id} risk assessment",
                score=risk_score,
                content={
                    "processed_id": processed_id,
                    "num_violations": len(violations),
                    "violations": [v.rule for v in violations],
                },
                created_at=datetime.now(timezone.utc),
            )
            db.add(report)
            db.commit()
            db.refresh(report)

            self.log(
                "assess_risk", {"processed_id": processed_id, "risk_score": risk_score}
            )

            return {"risk_score": risk_score, "report_id": report.id}
        finally:
            db.close()
