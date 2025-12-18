from datetime import datetime, timezone

from db import SessionLocal
from models import PolicyRule, ProcessedData, Violation
from sqlalchemy.orm import Session

from .base import BaseAgent


class ComplianceCheckerAgent(BaseAgent):
    def __init__(self):
        super().__init__(name="ComplianceChecker")

    def check_compliance(self, processed_id: int):
        db: Session = SessionLocal()

        try:
            processed_entry = (
                db.query(ProcessedData).filter(ProcessedData.id == processed_id).first()
            )
            if not processed_entry:
                self.log(
                    "check_compliance",
                    {"error": "processed_data not found", "processed_id": processed_id},
                )
                return None

            # Fetch all policy rules
            rules = db.query(PolicyRule).all()
            violations_found = []

            for rule in rules:
                # Minimal example check: if rule name appears in text, mark violation
                text_content = str(processed_entry.structured.get("raw_content", ""))
                if rule.name.lower() in text_content.lower():
                    violation = Violation(
                        rule=rule.name,
                        severity=rule.severity,
                        details={
                            "processed_id": processed_id,
                            "matched_text": rule.name,
                        },
                        created_at=datetime.now(timezone.utc),
                    )
                    db.add(violation)
                    violations_found.append(rule.name)

            db.commit()
            self.log(
                "check_compliance",
                {"processed_id": processed_id, "violations": violations_found},
            )
            return violations_found
        finally:
            db.close()
