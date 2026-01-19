from db import SessionLocal
from fastapi import APIRouter, Depends
from models import Report
from sqlalchemy import String, cast
from security import AuthContext, get_auth_context

router = APIRouter(prefix="/dashboard/reports", tags=["dashboard"])


@router.get("")
def list_reports(
    limit: int = 20,
    risk_tier: str | None = None,
    query: str | None = None,
    auth: AuthContext = Depends(get_auth_context),
):
    db = SessionLocal()

    try:
        query_builder = db.query(Report).filter(
            Report.org_id == auth.org_id,
            Report.workspace_id == auth.workspace_id,
        )
        if risk_tier:
            risk_clause = f'%\"risk_tier\": \"{risk_tier}\"%'
            query_builder = query_builder.filter(
                cast(Report.content, String).ilike(risk_clause)
            )
        if query:
            query_builder = query_builder.filter(Report.summary.ilike(f"%{query}%"))

        reports = (
            query_builder.order_by(Report.created_at.desc()).limit(limit).all()
        )

        return [
            {
                "id": r.id,
                "summary": r.summary,
                "risk_score": r.score,
                "risk_tier": (
                    r.content.get("risk_tier")
                    if isinstance(r.content, dict)
                    else None
                ),
                "created_at": (
                    r.created_at.isoformat() if r.created_at is not None else None
                ),
            }
            for r in reports
        ]
    finally:
        db.close()
