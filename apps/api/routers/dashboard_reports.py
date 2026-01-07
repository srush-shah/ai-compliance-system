from db import SessionLocal
from fastapi import APIRouter
from models import Report

router = APIRouter(prefix="/dashboard/reports", tags=["dashboard"])


@router.get("")
def list_reports(limit: int = 20):
    db = SessionLocal()

    try:
        reports = db.query(Report).order_by(Report.created_at.desc()).limit(limit).all()

        return [
            {
                "id": r.id,
                "summary": r.summary,
                "risk_score": r.score,
                "created_at": (
                    r.created_at.isoformat() if r.created_at is not None else None
                ),
            }
            for r in reports
        ]
    finally:
        db.close()
