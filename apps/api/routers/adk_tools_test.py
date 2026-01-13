from adk.tools.db_tools import (
    create_violation,
    get_policy_rules,
    get_processed_data_by_id,
    log_agent_action,
)
from fastapi import APIRouter, Depends
from security import AuthContext, get_auth_context

router = APIRouter(prefix="/test_tools", tags=["test_tools"])


@router.get("/processed/{pid}")
def test_processed(pid: int, auth: AuthContext = Depends(get_auth_context)):
    return get_processed_data_by_id(
        pid, org_id=auth.org_id, workspace_id=auth.workspace_id
    )


@router.get("/rules")
def test_rules(auth: AuthContext = Depends(get_auth_context)):
    return get_policy_rules(org_id=auth.org_id, workspace_id=auth.workspace_id)


@router.post("/violation")
def test_violation(
    pid: int,
    rule: str,
    severity: str,
    auth: AuthContext = Depends(get_auth_context),
):
    return create_violation(
        pid,
        rule,
        severity,
        {"test": "yes"},
        org_id=auth.org_id,
        workspace_id=auth.workspace_id,
    )


@router.post("/log")
def test_log(agent: str, action: str):
    return log_agent_action(agent, action, {"note": "tool test"})
