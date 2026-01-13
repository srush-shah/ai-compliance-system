import os
from datetime import datetime, timedelta, timezone
from typing import Optional

import jwt
from db import SessionLocal
from fastapi import APIRouter, Depends, Header, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from models import Org, Workspace
from pydantic import BaseModel
from sqlalchemy.orm import Session

router = APIRouter(prefix="/auth", tags=["auth"])
security_scheme = HTTPBearer()


class AuthContext(BaseModel):
    org_id: int
    workspace_id: int
    token_type: str
    subject: Optional[str] = None


class TokenRequest(BaseModel):
    org_id: Optional[int] = None
    workspace_id: Optional[int] = None


class TokenResponse(BaseModel):
    access_token: str
    expires_at: str


def _get_default_org_workspace() -> tuple[int, int]:
    org_id = os.getenv("DEFAULT_ORG_ID")
    workspace_id = os.getenv("DEFAULT_WORKSPACE_ID")
    if not org_id or not workspace_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Default org/workspace not configured",
        )
    return int(org_id), int(workspace_id)


def _validate_org_workspace(db: Session, org_id: int, workspace_id: int) -> None:
    org = db.query(Org).filter(Org.id == org_id).first()
    workspace = (
        db.query(Workspace)
        .filter(Workspace.id == workspace_id, Workspace.org_id == org_id)
        .first()
    )
    if not org or not workspace:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Invalid org/workspace",
        )


def _decode_jwt(token: str) -> dict:
    jwt_secret = os.getenv("JWT_SECRET")
    if not jwt_secret:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="JWT secret not configured",
        )

    options = {"require": ["exp"]}
    decode_kwargs: dict[str, object] = {
        "key": jwt_secret,
        "algorithms": ["HS256"],
        "options": options,
    }
    audience = os.getenv("JWT_AUDIENCE")
    issuer = os.getenv("JWT_ISSUER")
    if audience:
        decode_kwargs["audience"] = audience
    if issuer:
        decode_kwargs["issuer"] = issuer

    try:
        return jwt.decode(token, **decode_kwargs)
    except jwt.ExpiredSignatureError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token expired",
        ) from exc
    except jwt.PyJWTError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token",
        ) from exc


def get_auth_context(
    credentials: HTTPAuthorizationCredentials = Depends(security_scheme),
) -> AuthContext:
    token = credentials.credentials
    api_token = os.getenv("API_AUTH_TOKEN") or os.getenv("API_KEY")

    if api_token and token == api_token:
        org_id, workspace_id = _get_default_org_workspace()
        token_type = "api_key"
        subject = "api_key"
    else:
        payload = _decode_jwt(token)
        org_id = payload.get("org_id")
        workspace_id = payload.get("workspace_id")
        if org_id is None or workspace_id is None:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Token missing org/workspace",
            )
        token_type = "jwt"
        subject = payload.get("sub")

    db = SessionLocal()
    try:
        _validate_org_workspace(db, int(org_id), int(workspace_id))
    finally:
        db.close()

    return AuthContext(
        org_id=int(org_id),
        workspace_id=int(workspace_id),
        token_type=token_type,
        subject=subject,
    )


@router.post("/token", response_model=TokenResponse)
def issue_token(
    payload: TokenRequest,
    x_api_key: Optional[str] = Header(default=None, alias="X-API-Key"),
) -> TokenResponse:
    api_token = os.getenv("API_AUTH_TOKEN") or os.getenv("API_KEY")
    if not api_token or x_api_key != api_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid API key",
        )

    jwt_secret = os.getenv("JWT_SECRET")
    if not jwt_secret:
        raise HTTPException(
            status_code=status.HTTP_501_NOT_IMPLEMENTED,
            detail="JWT issuance not configured",
        )

    if payload.org_id is None or payload.workspace_id is None:
        org_id, workspace_id = _get_default_org_workspace()
    else:
        org_id = payload.org_id
        workspace_id = payload.workspace_id

    db = SessionLocal()
    try:
        _validate_org_workspace(db, int(org_id), int(workspace_id))
    finally:
        db.close()

    ttl_seconds = int(os.getenv("JWT_TTL_SECONDS", "3600"))
    now = datetime.now(timezone.utc)
    expires_at = now + timedelta(seconds=ttl_seconds)

    token_payload = {
        "sub": "api_key",
        "org_id": int(org_id),
        "workspace_id": int(workspace_id),
        "iat": int(now.timestamp()),
        "exp": int(expires_at.timestamp()),
    }
    issuer = os.getenv("JWT_ISSUER")
    audience = os.getenv("JWT_AUDIENCE")
    if issuer:
        token_payload["iss"] = issuer
    if audience:
        token_payload["aud"] = audience

    access_token = jwt.encode(token_payload, jwt_secret, algorithm="HS256")

    return TokenResponse(access_token=access_token, expires_at=expires_at.isoformat())
