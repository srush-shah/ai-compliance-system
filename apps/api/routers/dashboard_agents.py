from db import SessionLocal
from fastapi import APIRouter
from models import AgentLog

router = APIRouter(prefix="/dashboard/agents", tags=["dashboard"])


@router.get("")
def list_agent_logs(limit: int = 100):
    db = SessionLocal()

    try:
        logs = (
            db.query(AgentLog).order_by(AgentLog.created_at.desc()).limit(limit).all()
        )

        return [
            {
                "agent": log.agent_name,
                "action": log.action,
                "payload": log.details,
                "created_at": log.created_at,
            }
            for log in logs
        ]
    finally:
        db.close()
