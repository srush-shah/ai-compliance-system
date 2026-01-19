from db import SessionLocal
from fastapi import APIRouter, Depends
from models import Violation
from sqlalchemy import String, cast, or_
from security import AuthContext, get_auth_context

router = APIRouter(prefix="/dashboard/violations", tags=["dashboard"])


@router.get("")
def list_violations(
    limit: int = 50,
    severity: str | None = None,
    query: str | None = None,
    auth: AuthContext = Depends(get_auth_context),
):
    db = SessionLocal()

    try:
        query_builder = db.query(Violation).filter(
            Violation.org_id == auth.org_id,
            Violation.workspace_id == auth.workspace_id,
        )

        if severity:
            query_builder = query_builder.filter(Violation.severity == severity)
        if query:
            like_query = f"%{query}%"
            query_builder = query_builder.filter(
                or_(
                    Violation.rule.ilike(like_query),
                    cast(Violation.details, String).ilike(like_query),
                )
            )

        violations = (
            query_builder.order_by(Violation.created_at.desc()).limit(limit).all()
        )

        return [
            {
                "id": v.id,
                "rule": v.rule,
                "severity": v.severity,
                "details": v.details,
                "created_at": (
                    v.created_at.isoformat() if v.created_at is not None else None
                ),
            }
            for v in violations
        ]
    finally:
        db.close()
