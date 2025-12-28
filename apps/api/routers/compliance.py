from adk.workflows.compliance_workflow import ComplianceReviewWorkflow
from fastapi import APIRouter, HTTPException

router = APIRouter(prefix="/compliance", tags=["compliance"])

workflow = ComplianceReviewWorkflow()


@router.post("/run/{raw_id}")
def run_compliance(raw_id: int):
    try:
        result = workflow.run(raw_id=raw_id)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/retry/{raw_id}")
def retry_compliance(raw_id: int):
    return workflow.retry(raw_id=raw_id)
