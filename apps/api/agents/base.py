from db import SessionLocal
from models import AgentLog


class BaseAgent:
    def __init__(self, name: str):
        self.name = name

    def log(self, action: str, details: dict = None):
        db = SessionLocal()

        try:
            log_entry = AgentLog(
                agent_name=self.name, action=action, details=details or {}
            )
            db.add(log_entry)
            db.commit()
        finally:
            db.close()
