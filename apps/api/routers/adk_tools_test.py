from adk.tools.db_tools import (
    create_violation,
    fetch_policy_rules,
    fetch_processed_data,
    log_agent_action,
)
from fastapi import APIRouter

router = APIRouter(prefix="/test_tools", tags=["test_tools"])


@router.get("/processed/{pid}")
def test_processed(pid: int):
    return fetch_processed_data(pid)


@router.get("/rules")
def test_rules():
    return fetch_policy_rules()


@router.post("/violation")
def test_violation(pid: int, rule: str, severity: str):
    return create_violation(pid, rule, severity, {"test": "yes"})


@router.post("/log")
def test_log(agent: str, action: str):
    return log_agent_action(agent, action, {"note": "tool test"})
