from typing import Any, Dict, List, Optional

from adk.tools.tools_registry import get_adk_tools
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

router = APIRouter(prefix="/policy-rules", tags=["policy-rules"])
tools = get_adk_tools()


class PolicyRuleCreate(BaseModel):
    name: str
    description: Optional[str] = None
    severity: str = Field(default="medium")
    category: str = Field(default="general")
    pattern_type: str = Field(default="keyword")
    pattern: Optional[str] = None
    scope: Optional[Any] = None
    remediation: Optional[str] = None
    is_active: bool = True
    actor: Optional[str] = None


class PolicyRuleUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    severity: Optional[str] = None
    category: Optional[str] = None
    pattern_type: Optional[str] = None
    pattern: Optional[str] = None
    scope: Optional[Any] = None
    remediation: Optional[str] = None
    is_active: Optional[bool] = None
    actor: Optional[str] = None


@router.get("")
def list_policy_rules() -> List[Dict[str, Any]]:
    rules = tools["get_policy_rules"]()
    if rules and isinstance(rules, list) and rules[0].get("error") == "no policies found":
        return []
    return rules


@router.get("/{rule_id}")
def get_policy_rule(rule_id: int) -> Dict[str, Any]:
    rule = tools["get_policy_rule_by_id"](rule_id)
    if "error" in rule:
        raise HTTPException(status_code=404, detail="Rule not found")
    return rule


@router.get("/{rule_id}/versions")
def get_policy_rule_versions(rule_id: int) -> List[Dict[str, Any]]:
    versions = tools["list_policy_rule_versions"](rule_id)
    return versions


@router.post("")
def create_policy_rule(payload: PolicyRuleCreate) -> Dict[str, Any]:
    result = tools["create_policy_rule"](
        name=payload.name,
        description=payload.description,
        severity=payload.severity,
        category=payload.category,
        pattern_type=payload.pattern_type,
        pattern=payload.pattern,
        scope=payload.scope,
        remediation=payload.remediation,
        is_active=payload.is_active,
        actor=payload.actor,
    )
    return result


@router.put("/{rule_id}")
def update_policy_rule(rule_id: int, payload: PolicyRuleUpdate) -> Dict[str, Any]:
    updates = payload.model_dump(exclude_unset=True)
    actor = updates.pop("actor", None)

    if not updates:
        raise HTTPException(status_code=400, detail="No updates provided")

    result = tools["update_policy_rule"](rule_id=rule_id, updates=updates, actor=actor)
    if "error" in result:
        raise HTTPException(status_code=404, detail="Rule not found")
    return result


@router.delete("/{rule_id}")
def deactivate_policy_rule(rule_id: int, actor: Optional[str] = None) -> Dict[str, Any]:
    result = tools["deactivate_policy_rule"](rule_id, actor)
    if "error" in result:
        raise HTTPException(status_code=404, detail="Rule not found")
    return result
