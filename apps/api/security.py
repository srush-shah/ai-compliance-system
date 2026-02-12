import os
from datetime import datetime, timezone
from typing import cast

from db import SessionLocal
from fastapi import HTTPException, status
from models import Org, Workspace
from pydantic import BaseModel
from sqlalchemy.orm import Session


class AuthContext(BaseModel):
    org_id: int
    workspace_id: int
    token_type: str = "none"
    subject: str | None = None


def _validate_org_workspace(db: Session, org_id: int, workspace_id: int) -> None:
    org = db.query(Org).filter(Org.id == org_id).first()
    workspace = (
        db.query(Workspace)
        .filter(Workspace.id == workspace_id, Workspace.org_id == org_id)
        .first()
    )
    if not org or not workspace:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Org/workspace not initialized",
        )


def _resolve_org_workspace(db: Session) -> tuple[int, int]:
    default_org_id = os.getenv("DEFAULT_ORG_ID")
    default_workspace_id = os.getenv("DEFAULT_WORKSPACE_ID")
    if default_org_id and default_workspace_id:
        org_id = int(default_org_id)
        workspace_id = int(default_workspace_id)
        _validate_org_workspace(db, org_id, workspace_id)
        return org_id, workspace_id

    first_workspace = db.query(Workspace).order_by(Workspace.id.asc()).first()
    if not first_workspace:
        org = Org(
            name=os.getenv("DEFAULT_ORG_NAME", "Default Organization"),
            created_at=datetime.now(timezone.utc),
        )
        db.add(org)
        db.commit()
        db.refresh(org)

        first_workspace = Workspace(
            org_id=cast(int, org.id),
            name=os.getenv("DEFAULT_WORKSPACE_NAME", "Default Workspace"),
            created_at=datetime.now(timezone.utc),
        )
        db.add(first_workspace)
        db.commit()
        db.refresh(first_workspace)

    org_id = cast(int, first_workspace.org_id)
    workspace_id = cast(int, first_workspace.id)
    _validate_org_workspace(db, org_id, workspace_id)
    return org_id, workspace_id


def get_auth_context() -> AuthContext:
    db = SessionLocal()
    try:
        org_id, workspace_id = _resolve_org_workspace(db)
    finally:
        db.close()

    return AuthContext(
        org_id=org_id,
        workspace_id=workspace_id,
        token_type="none",
        subject="anonymous",
    )


def get_auth_context_for_token(token: str | None = None) -> AuthContext:
    _ = token
    return get_auth_context()
