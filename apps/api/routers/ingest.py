from agents.data_engineer import DataEngineerAgent
from db import SessionLocal
from fastapi import APIRouter

router = APIRouter(prefix="/ingest", tags=["ingest"])


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@router.post("")
def run_data_engineer(raw_id: int):
    agent = DataEngineerAgent()
    processed_id = agent.process_raw_data(raw_id)
    if processed_id is None:
        return {"status": "failed", "raw_id": raw_id}

    return {"status": "processed", "processed_id": processed_id}
