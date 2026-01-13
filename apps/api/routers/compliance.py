from adk.tools.tools_registry import get_adk_tools
from fastapi import APIRouter, BackgroundTasks, HTTPException, Depends
from security import AuthContext, get_auth_context
from services.compliance_runner import run_compliance_workflow

router = APIRouter(prefix="/compliance", tags=["compliance"])
tools = get_adk_tools()


@router.post("/run/{raw_id}")
def run_compliance(
    raw_id: int,
    background_tasks: BackgroundTasks,
    auth: AuthContext = Depends(get_auth_context),
):
    raw = tools["get_raw_data_by_id"](
        raw_id, org_id=auth.org_id, workspace_id=auth.workspace_id
    )
    if "error" in raw:
        raise HTTPException(status_code=404, detail="Raw data not found")

    active = tools["get_active_adk_run_by_raw_id"](
        raw_id, org_id=auth.org_id, workspace_id=auth.workspace_id
    )

    if active.get("active"):
        return {"status": "already_running", "run_id": active["run_id"]}

    adk_run = tools["create_adk_run"](raw_id=raw_id, status="started")

    background_tasks.add_task(run_compliance_workflow, raw_id, adk_run["id"], False)

    return {"status": "started", "run_id": adk_run["id"]}


@router.post("/retry/{raw_id}")
def retry_compliance(
    raw_id: int,
    background_tasks: BackgroundTasks,
    auth: AuthContext = Depends(get_auth_context),
):
    raw = tools["get_raw_data_by_id"](
        raw_id, org_id=auth.org_id, workspace_id=auth.workspace_id
    )
    if "error" in raw:
        raise HTTPException(status_code=404, detail="Raw data not found")

    latest = tools["get_latest_adk_run_by_raw_id"](
        raw_id, org_id=auth.org_id, workspace_id=auth.workspace_id
    )

    if "id" not in latest and "error" in latest:
        raise HTTPException(status_code=404, detail="No previous run found")

    if latest["status"] != "failed":
        return {
            "status": "not_allowed",
            "message": "Only failed runs can be retried",
            "run_id": latest["id"],
        }

    retryable_error_codes = [
        "DATA_ENGINEERING_FAILED",
        "COMPLIANCE_CHECK_FAILED",
        "GOOGLE_ADK_NO_FINAL_OUTPUT",
        "GOOGLE_ADK_FAILED",
        "GOOGLE_ADK_EXCEPTION",
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
def list_runs(limit: int = 20, auth: AuthContext = Depends(get_auth_context)):
    return tools["list_adk_runs"](
        limit=limit, org_id=auth.org_id, workspace_id=auth.workspace_id
    )


@router.get("/runs/{run_id}")
def get_run(run_id: int, auth: AuthContext = Depends(get_auth_context)):
    result = tools["get_adk_run_by_id"](
        run_id, org_id=auth.org_id, workspace_id=auth.workspace_id
    )

    if "id" not in result and "error" in result:
        raise HTTPException(status_code=404, detail="Run not found")

    return result


@router.get("/runs/raw/{raw_id}")
def get_runs_for_raw(raw_id: int, auth: AuthContext = Depends(get_auth_context)):
    return tools["list_adk_runs_by_raw_id"](
        raw_id, org_id=auth.org_id, workspace_id=auth.workspace_id
    )


@router.get("/runs/{run_id}/steps")
def get_runs_steps(run_id: int, auth: AuthContext = Depends(get_auth_context)):
    return tools["get_adk_run_steps"](
        run_id, org_id=auth.org_id, workspace_id=auth.workspace_id
    )
