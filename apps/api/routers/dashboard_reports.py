from db import SessionLocal
from fastapi import APIRouter, Depends
from models import Report
from security import AuthContext, get_auth_context

router = APIRouter(prefix="/dashboard/reports", tags=["dashboard"])


@router.get("")
def list_reports(limit: int = 20, auth: AuthContext = Depends(get_auth_context)):
    db = SessionLocal()

    try:
        reports = (
            db.query(Report)
            .filter(
                Report.org_id == auth.org_id,
                Report.workspace_id == auth.workspace_id,
            )
            .order_by(Report.created_at.desc())
            .limit(limit)
            .all()
        )

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
