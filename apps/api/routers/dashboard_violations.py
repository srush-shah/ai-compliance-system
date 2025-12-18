from db import SessionLocal
from fastapi import APIRouter
from models import Violation

router = APIRouter(prefix="/dashboard/violations", tags=["dashboard"])


@router.get("")
def list_violations(limit: int = 50):
    db = SessionLocal()

    try:
        violations = (
            db.query(Violation).order_by(Violation.created_at.desc()).limit(limit).all()
        )

        return [
            {
                "id": v.id,
                "rule": v.rule,
                "severity": v.severity,
                "details": v.details,
                "created_at": v.created_at.isoformat() if v.created_at else None,
            }
            for v in violations
        ]
    finally:
        db.close()
