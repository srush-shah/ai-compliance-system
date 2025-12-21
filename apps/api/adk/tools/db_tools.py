from datetime import datetime, timezone
from this import d
from typing import Dict, List

from db import SessionLocal
from models import AgentLog, PolicyRule, ProcessedData, Violation
from sqlalchemy.orm import Session


def fetch_processed_data(processed_id: int) -> Dict:
    db: Session = SessionLocal()

    try:
        p = db.query(ProcessedData).filter(ProcessedData.id == processed_id).first()

        if p is None:
            return {"error": "not_found"}

        return {
            "id": p.id,
            "structured": p.structured,
            "created_at": p.created_at.isoformat() if p.created_at else None,
        }
    finally:
        db.close()


def fetch_policy_rules() -> List[Dict]:
    db: Session = SessionLocal()

    try:
        rules = db.query(PolicyRule).all()

        if rules is None:
            return {"error": "no policies found"}

        return [
            {
                "id": r.id,
                "name": r.name,
                "description": r.description,
                "severity": r.severity,
            }
            for r in rules
        ]
    finally:
        db.close()


def create_violation(
    processed_id: int, rule: str, severity: str, details: Dict
) -> Dict:

    db: Session = SessionLocal()

    try:
        v = Violation(
            rule=rule,
            severity=severity,
            details={"processed_id": processed_id, **details},
            created_at=datetime.now(timezone.utc),
        )
        db.add(v)
        db.commit()
        db.refresh(v)
        return {"id": v.id, "processed_id": processed_id}
    finally:
        db.close()


def log_agent_action(agent_name: str, action: str, details: Dict) -> Dict:

    db: Session = SessionLocal()

    try:
        log = AgentLog(
            agent_name=agent_name,
            action=action,
            details=details,
            created_at=datetime.now(timezone.utc),
        )
        db.add(log)
        db.commit()
        db.refresh(log)
        return {"id": log.id}
    finally:
        db.close()
