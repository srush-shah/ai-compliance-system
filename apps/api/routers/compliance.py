from agents.compliance_checker import ComplianceCheckerAgent
from fastapi import APIRouter

router = APIRouter(prefix="/check_compliance", tags=["compliance"])


@router.post("")
def run_compliance(processed_id: int):
    agent = ComplianceCheckerAgent()
    violations = agent.check_compliance(processed_id)
    if violations is None:
        return {"status": "failed", "processed_id": processed_id}

    return {"status": "checked", "violations": violations}
