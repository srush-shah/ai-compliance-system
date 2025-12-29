from adk.tools.tools_registry import get_adk_tools
from fastapi import APIRouter

router = APIRouter(prefix="/dashboard/runs", tags=["dashboard"])
tools = get_adk_tools()


@router.get("")
def list_runs(limit: int = 20):
    return tools["list_adk_runs"](limit=limit)


@router.get("/{run_id}")
def get_run(run_id: int):
    return tools["get_adk_run_by_id"](run_id)


@router.get("/{run_id}/steps")
def get_run_steps(run_id: int):
    return tools["get_adk_run_steps"](run_id)
