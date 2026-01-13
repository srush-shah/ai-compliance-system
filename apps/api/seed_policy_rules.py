"""Seed realistic policy rules with structured fields."""

import os
from datetime import datetime, timezone

from db import SessionLocal
from models import Org, PolicyRule, PolicyRuleAudit, PolicyRuleVersion, Workspace

SEED_RULES = [
    {
        "name": "Mask Social Security Numbers",
        "description": "SSNs must be masked unless stored in approved PII fields.",
        "severity": "high",
        "category": "PII",
        "pattern_type": "regex",
        "pattern": "\\b\\d{3}-\\d{2}-\\d{4}\\b",
        "scope": ["body", "attachments"],
        "remediation": "Replace SSNs with masked format (***-**-1234).",
    },
    {
        "name": "No credit card numbers in notes",
        "description": "Payment card data must not appear in free-form notes.",
        "severity": "critical",
        "category": "PCI",
        "pattern_type": "regex",
        "pattern": "\\b(?:\\d[ -]*?){13,16}\\b",
        "scope": ["notes"],
        "remediation": "Remove card numbers and store tokenized reference instead.",
    },
    {
        "name": "HIPAA terms require consent",
        "description": "Clinical data references must include consent statement.",
        "severity": "medium",
        "category": "Healthcare",
        "pattern_type": "keyword",
        "pattern": "HIPAA",
        "scope": ["body"],
        "remediation": "Append consent clause or redact clinical references.",
    },
    {
        "name": "Export-controlled terms",
        "description": "Export-controlled terms require legal review.",
        "severity": "high",
        "category": "Export",
        "pattern_type": "keyword",
        "pattern": "export-controlled",
        "scope": ["body", "attachments"],
        "remediation": "Escalate to legal and mark as export-controlled.",
    },
    {
        "name": "Confidential pricing language",
        "description": "Pricing clauses must include confidentiality tag.",
        "severity": "low",
        "category": "Commercial",
        "pattern_type": "semantic",
        "pattern": "pricing confidentiality clause",
        "scope": ["sections"],
        "remediation": "Add confidentiality designation to pricing section.",
    },
]


def main() -> None:
    db = SessionLocal()
    try:
        default_org_id = os.getenv("DEFAULT_ORG_ID")
        default_workspace_id = os.getenv("DEFAULT_WORKSPACE_ID")
        org_id = int(default_org_id) if default_org_id else None
        workspace_id = int(default_workspace_id) if default_workspace_id else None

        if org_id is None or workspace_id is None:
            org = db.query(Org).order_by(Org.id.asc()).first()
            if org is None:
                org = Org(name="Default Org", created_at=datetime.now(timezone.utc))
                db.add(org)
                db.commit()
                db.refresh(org)
            workspace = (
                db.query(Workspace)
                .filter(Workspace.org_id == org.id)
                .order_by(Workspace.id.asc())
                .first()
            )
            if workspace is None:
                workspace = Workspace(
                    org_id=org.id,
                    name="Default Workspace",
                    created_at=datetime.now(timezone.utc),
                )
                db.add(workspace)
                db.commit()
                db.refresh(workspace)

            org_id = org.id
            workspace_id = workspace.id

        for rule_data in SEED_RULES:
            existing = (
                db.query(PolicyRule)
                .filter(PolicyRule.name == rule_data["name"])
                .first()
            )
            if existing:
                continue

            rule = PolicyRule(
                org_id=org_id,
                workspace_id=workspace_id,
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
                    actor="seed_script",
                    changes=snapshot,
                    created_at=datetime.now(timezone.utc),
                )
            )
            db.commit()
    finally:
        db.close()


if __name__ == "__main__":
    main()
    print("Seeded policy rules.")
