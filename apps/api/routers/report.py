from agents.report_writer import ReportWriterAgent
from fastapi import APIRouter

router = APIRouter(prefix="/generate-report", tags=["report"])


@router.post("")
def generate_report(report_id: int):
    agent = ReportWriterAgent()
    result = agent.generate_report(report_id)
    if result is None:
        return {"status": "failed", "report_id": report_id}
    return {"status": "generated", "report": result}
