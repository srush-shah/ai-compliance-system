from adk.tools.db_tools import (
    create_violation,
    get_policy_rules,
    get_processed_data_by_id,
    log_agent_action,
)
from fastapi import APIRouter

router = APIRouter(prefix="/test_tools", tags=["test_tools"])


@router.get("/processed/{pid}")
def test_processed(pid: int):
    return get_processed_data_by_id(pid)


@router.get("/rules")
def test_rules():
    return get_policy_rules()


@router.post("/violation")
def test_violation(pid: int, rule: str, severity: str):
    return create_violation(pid, rule, severity, {"test": "yes"})


@router.post("/log")
def test_log(agent: str, action: str):
    return log_agent_action(agent, action, {"note": "tool test"})
