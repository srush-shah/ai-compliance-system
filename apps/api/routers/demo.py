from datetime import datetime, timezone

from adk.tools.tools_registry import get_adk_tools
from db import SessionLocal
from fastapi import APIRouter, BackgroundTasks, Depends
from models import PolicyRule, PolicyRuleAudit, PolicyRuleVersion, RawData
from seed.demo_documents import DEMO_DOCUMENTS
from seed.demo_policy_rules import DEMO_POLICY_RULES
from security import AuthContext, get_auth_context
from services.compliance_runner import run_compliance_workflow
from sqlalchemy.orm import Session

router = APIRouter(prefix="/demo", tags=["demo"])
tools = get_adk_tools()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@router.post("/load")
def load_demo_data(
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    auth: AuthContext = Depends(get_auth_context),
):
    for rule_data in DEMO_POLICY_RULES:
        existing = (
            db.query(PolicyRule)
            .filter(
                PolicyRule.org_id == auth.org_id,
                PolicyRule.workspace_id == auth.workspace_id,
                PolicyRule.name == rule_data["name"],
            )
            .first()
        )
        if existing:
            continue

        rule = PolicyRule(
            org_id=auth.org_id,
            workspace_id=auth.workspace_id,
            name=rule_data["name"],
            description=rule_data["description"],
            severity=rule_data["severity"],
            category=rule_data["category"],
            pattern_type=rule_data["pattern_type"],
            pattern=rule_data["pattern"],
            scope=rule_data["scope"],
            remediation=rule_data["remediation"],
            version="v1",
            is_active=1,
            created_at=datetime.now(timezone.utc),
        )
        db.add(rule)
        db.commit()
        db.refresh(rule)

        snapshot = {
            "name": rule.name,
            "description": rule.description,
            "severity": rule.severity,
            "category": rule.category,
            "pattern_type": rule.pattern_type,
            "pattern": rule.pattern,
            "scope": rule.scope,
            "remediation": rule.remediation,
            "version": rule.version,
            "is_active": True,
        }
        db.add(
            PolicyRuleVersion(
                rule_id=rule.id,
                version=rule.version,
                content_snapshot=snapshot,
                created_at=datetime.now(timezone.utc),
            )
        )
        db.add(
            PolicyRuleAudit(
                rule_id=rule.id,
                action="seeded",
                actor="demo_loader",
                changes=snapshot,
                created_at=datetime.now(timezone.utc),
            )
        )
        db.commit()

    demo_document = DEMO_DOCUMENTS[0]
    content = demo_document["content"]

    record = RawData(
        org_id=auth.org_id,
        workspace_id=auth.workspace_id,
        content=content,
        file_name=demo_document["file_name"],
        file_type=demo_document["file_type"],
        source="demo",
    )
    db.add(record)
    db.commit()
    db.refresh(record)

    adk_run = tools["create_adk_run"](raw_id=record.id, status="queued")
    background_tasks.add_task(
        run_compliance_workflow,
        record.id,
        adk_run["id"],
        False,
    )

    return {"raw_data_id": record.id, "run_id": adk_run["id"]}
