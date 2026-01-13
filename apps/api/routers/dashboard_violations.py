from db import SessionLocal
from fastapi import APIRouter, Depends
from models import Violation
from security import AuthContext, get_auth_context

router = APIRouter(prefix="/dashboard/violations", tags=["dashboard"])


@router.get("")
def list_violations(limit: int = 50, auth: AuthContext = Depends(get_auth_context)):
    db = SessionLocal()

    try:
        violations = (
            db.query(Violation)
            .filter(
                Violation.org_id == auth.org_id,
                Violation.workspace_id == auth.workspace_id,
            )
            .order_by(Violation.created_at.desc())
            .limit(limit)
            .all()
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
