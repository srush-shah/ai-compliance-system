from adk.tools.tools_registry import get_adk_tools
from fastapi import APIRouter, BackgroundTasks, HTTPException
from services.compliance_runner import run_compliance_workflow

router = APIRouter(prefix="/compliance", tags=["compliance"])
tools = get_adk_tools()


@router.post("/run/{raw_id}")
def run_compliance(raw_id: int, background_tasks: BackgroundTasks):
    active = tools["get_active_adk_run_by_raw_id"](raw_id)

    if active.get("active"):
        return {"status": "already_running", "run_id": active["run_id"]}

    adk_run = tools["create_adk_run"](raw_id=raw_id, status="started")

    background_tasks.add_task(run_compliance_workflow, raw_id, adk_run["id"], False)

    return {"status": "started", "run_id": adk_run["id"]}


@router.post("/retry/{raw_id}")
def retry_compliance(raw_id: int, background_tasks: BackgroundTasks):
    latest = tools["get_latest_adk_run_by_raw_id"](raw_id)

    if "id" not in latest and "error" in latest:
        raise HTTPException(status_code=404, detail="No previous run found")

    if latest["status"] != "failed":
        return {
            "status": "not_allowed",
            "messsage": "Only failed runs can be retried",
            "run_id": latest["id"],
        }

    retryable_error_codes = [
        "DATA_ENGINEERING_FAILED",
        "COMPLIANCE_CHECK_FAILED",
    ]

    if latest.get("error_code") not in retryable_error_codes:
        return {
            "status": "not_allowed",
            "message": "Failure type is not retryable",
            "run_id": latest["id"],
            "error_code": latest.get("error_code"),
        }

    adk_run = tools["create_adk_run"](raw_id=raw_id, status="started")

    background_tasks.add_task(run_compliance_workflow, raw_id, adk_run["id"], True)

    return {"status": "started", "run_id": adk_run["id"], "retry_of": latest["id"]}


@router.get("/runs")
def list_runs(limit: int = 20):
    return tools["list_adk_runs"](limit=limit)


@router.get("/runs/{run_id}")
def get_run(run_id: int):
    result = tools["get_adk_run_by_id"](run_id)

    if "id" not in result and "error" in result:
        raise HTTPException(status_code=404, detail="Run not found")

    return result


@router.get("/runs/raw/{raw_id}")
def get_runs_for_raw(raw_id: int):
    return tools["list_adk_runs_by_raw_id"](raw_id)


@router.get("/runs/{run_id}/steps")
def get_runs_steps(run_id: int):
    return tools["get_adk_run_steps"](run_id)
