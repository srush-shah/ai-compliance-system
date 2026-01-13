from adk.tools.tools_registry import get_adk_tools
from fastapi import APIRouter, Depends
from security import AuthContext, get_auth_context

router = APIRouter(prefix="/dashboard/runs", tags=["dashboard"])
tools = get_adk_tools()


@router.get("")
def list_runs(limit: int = 20, auth: AuthContext = Depends(get_auth_context)):
    return tools["list_adk_runs"](
        limit=limit, org_id=auth.org_id, workspace_id=auth.workspace_id
    )


@router.get("/{run_id}")
def get_run(run_id: int, auth: AuthContext = Depends(get_auth_context)):
    return tools["get_adk_run_by_id"](
        run_id, org_id=auth.org_id, workspace_id=auth.workspace_id
    )


@router.get("/{run_id}/steps")
def get_run_steps(run_id: int, auth: AuthContext = Depends(get_auth_context)):
    return tools["get_adk_run_steps"](
        run_id, org_id=auth.org_id, workspace_id=auth.workspace_id
    )
