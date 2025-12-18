from agents.risk_assessor import RiskAssessorAgent
from fastapi import APIRouter

router = APIRouter(prefix="/risk_assessment", tags=["risk"])


@router.post("")
def run_risk_assessment(processed_id: int):
    agent = RiskAssessorAgent()
    result = agent.assess_risk(processed_id)
    if result is None:
        return {"status": "failed", "processed_id": processed_id}
    return {
        "status": "assessed",
        "risk_score": result["risk_score"],
        "report_id": result["report_id"],
    }
