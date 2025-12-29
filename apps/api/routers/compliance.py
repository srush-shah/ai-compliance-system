from adk.workflows.compliance_workflow import ComplianceReviewWorkflow
from fastapi import APIRouter, HTTPException

from adk.tools.tools_registry import get_adk_tools

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


@router.get("/runs")
def list_runs(limit: int = 20):
    tools = get_adk_tools()
    return tools["list_adk_runs"](limit=limit)


@router.get("/runs/{run_id}")
def get_run(run_id: int):
    tools = get_adk_tools()
    result = tools["get_adk_run_by_id"](run_id)

    if "id" not in result and "error" in result:
        raise HTTPException(status_code=404, detail="Run not found")

    return result


@router.get("/runs/raw/{raw_id}")
def get_runs_for_raw(raw_id: int):
    tools = get_adk_tools()

    return tools["list_adk_runs_by_raw_id"](raw_id)


@router.get("/runs/{run_id}/steps")
def get_runs_steps(run_id: int):
    tools = get_adk_tools()
    return tools["get_adk_run_steps"](run_id)
