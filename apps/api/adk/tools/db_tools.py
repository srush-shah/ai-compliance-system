from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from db import SessionLocal
from models import (
    ADKRun,
    ADKRunStep,
    AgentLog,
    PolicyRule,
    PolicyRuleAudit,
    PolicyRuleVersion,
    ProcessedData,
    RawData,
    Report,
    Violation,
)
from sqlalchemy import Integer, cast, text
from sqlalchemy.orm import Session


def _calculate_duration_seconds(
    start: Optional[datetime], end: Optional[datetime]
) -> Optional[float]:
    """Safely calculate duration in seconds between two datetimes, handling timezone differences."""
    if not start or not end:
        return None

    # Ensure both datetimes are timezone-aware
    if start.tzinfo is None:
        start = start.replace(tzinfo=timezone.utc)
    if end.tzinfo is None:
        end = end.replace(tzinfo=timezone.utc)

    return (end - start).total_seconds()


def _apply_org_workspace_filters(
    query, model, org_id: int | None, workspace_id: int | None
):
    if org_id is not None:
        query = query.filter(model.org_id == org_id)
    if workspace_id is not None:
        query = query.filter(model.workspace_id == workspace_id)
    return query


def _get_org_workspace_for_raw(
    db: Session, raw_id: int
) -> Optional[tuple[int, int]]:
    raw = db.query(RawData).filter(RawData.id == raw_id).first()
    if not raw:
        return None
    return raw.org_id, raw.workspace_id


def _get_org_workspace_for_processed(
    db: Session, processed_id: int
) -> Optional[tuple[int, int]]:
    processed = (
        db.query(ProcessedData).filter(ProcessedData.id == processed_id).first()
    )
    if not processed:
        return None
    return processed.org_id, processed.workspace_id


# =========Read Ops==================


def get_raw_data_by_id(
    raw_id: int, org_id: int | None = None, workspace_id: int | None = None
) -> Dict:
    db: Session = SessionLocal()

    try:
        query = db.query(RawData).filter(RawData.id == raw_id)
        query = _apply_org_workspace_filters(query, RawData, org_id, workspace_id)
        r = query.first()

        if r is None:
            return {"error": "not_found"}

        return {
            "id": r.id,
            "org_id": r.org_id,
            "workspace_id": r.workspace_id,
            "content": r.content,
            "created_at": (
                r.created_at.isoformat() if r.created_at is not None else None
            ),
        }
    finally:
        db.close()


def get_processed_data_by_id(
    processed_id: int, org_id: int | None = None, workspace_id: int | None = None
) -> Dict:
    db: Session = SessionLocal()

    try:
        query = db.query(ProcessedData).filter(ProcessedData.id == processed_id)
        query = _apply_org_workspace_filters(query, ProcessedData, org_id, workspace_id)
        p = query.first()

        if p is None:
            return {"error": "not_found"}

        return {
            "id": p.id,
            "org_id": p.org_id,
            "workspace_id": p.workspace_id,
            "structured": p.structured,
            "created_at": (
                p.created_at.isoformat() if p.created_at is not None else None
            ),
        }
    finally:
        db.close()


def get_policy_rules(
    org_id: int | None = None, workspace_id: int | None = None
) -> List[Dict]:
    db: Session = SessionLocal()

    try:
        query = db.query(PolicyRule)
        query = _apply_org_workspace_filters(query, PolicyRule, org_id, workspace_id)
        rules = query.order_by(PolicyRule.id.asc()).all()

        if not rules:
            return [{"error": "no policies found"}]

        return [
            {
                "id": r.id,
                "name": r.name,
                "description": r.description,
                "severity": r.severity,
                "category": r.category,
                "pattern_type": r.pattern_type,
                "pattern": r.pattern,
                "scope": r.scope,
                "remediation": r.remediation,
                "version": r.version,
                "is_active": bool(r.is_active),
                "created_at": (
                    r.created_at.isoformat() if r.created_at is not None else None
                ),
                "updated_at": (
                    r.updated_at.isoformat() if r.updated_at is not None else None
                ),
            }
            for r in rules
        ]
    finally:
        db.close()


def get_policy_rule_by_id(
    rule_id: int, org_id: int | None = None, workspace_id: int | None = None
) -> Dict:
    db: Session = SessionLocal()
    try:
        query = db.query(PolicyRule).filter(PolicyRule.id == rule_id)
        query = _apply_org_workspace_filters(query, PolicyRule, org_id, workspace_id)
        rule = query.first()
        if rule is None:
            return {"error": "not_found"}

        return {
            "id": rule.id,
            "name": rule.name,
            "description": rule.description,
            "severity": rule.severity,
            "category": rule.category,
            "pattern_type": rule.pattern_type,
            "pattern": rule.pattern,
            "scope": rule.scope,
            "remediation": rule.remediation,
            "version": rule.version,
            "is_active": bool(rule.is_active),
            "created_at": (
                rule.created_at.isoformat() if rule.created_at is not None else None
            ),
            "updated_at": (
                rule.updated_at.isoformat() if rule.updated_at is not None else None
            ),
        }
    finally:
        db.close()


def list_policy_rule_versions(
    rule_id: int, org_id: int | None = None, workspace_id: int | None = None
) -> List[Dict]:
    db: Session = SessionLocal()
    try:
        query = db.query(PolicyRuleVersion).filter(
            PolicyRuleVersion.rule_id == rule_id
        )
        if org_id is not None or workspace_id is not None:
            query = query.join(
                PolicyRule, PolicyRuleVersion.rule_id == PolicyRule.id
            )
            query = _apply_org_workspace_filters(
                query, PolicyRule, org_id, workspace_id
            )
        versions = query.order_by(PolicyRuleVersion.id.asc()).all()

        return [
            {
                "id": v.id,
                "rule_id": v.rule_id,
                "version": v.version,
                "content_snapshot": v.content_snapshot,
                "created_at": (
                    v.created_at.isoformat() if v.created_at is not None else None
                ),
            }
            for v in versions
        ]
    finally:
        db.close()


def get_violations_by_processed_id(
    processed_id: int, org_id: int | None = None, workspace_id: int | None = None
) -> List[Dict]:
    db: Session = SessionLocal()

    try:
        query = db.query(Violation).filter(
            cast(text("violations.details ->> 'processed_id'"), Integer)
            == processed_id
        )
        query = _apply_org_workspace_filters(query, Violation, org_id, workspace_id)
        violations = query.all()

        return [
            {
                "id": v.id,
                "rule": v.rule,
                "severity": v.severity,
                "details": v.details,
                "created_at": (
                    v.created_at.isoformat() if v.created_at is not None else None
                ),
            }
            for v in violations
        ]
    finally:
        db.close()


def get_report_by_id(
    report_id: int, org_id: int | None = None, workspace_id: int | None = None
) -> Dict:
    db: Session = SessionLocal()
    try:
        query = db.query(Report).filter(Report.id == report_id)
        query = _apply_org_workspace_filters(query, Report, org_id, workspace_id)
        r = query.first()
        if not r:
            return {"error": "not_found"}

        return {
            "id": r.id,
            "summary": r.summary,
            "score": r.score,
            "content": r.content,
            "created_at": (
                r.created_at.isoformat() if r.created_at is not None else None
            ),
        }

    finally:
        db.close()


def get_active_adk_run_by_raw_id(
    raw_id: int, org_id: int | None = None, workspace_id: int | None = None
) -> Dict:
    db: Session = SessionLocal()
    try:
        query = db.query(ADKRun).filter(
            ADKRun.raw_id == raw_id, ADKRun.status == "started"
        )
        query = _apply_org_workspace_filters(query, ADKRun, org_id, workspace_id)
        run = query.first()

        if not run:
            return {"active": False}

        return {"active": True, "run_id": run.id, "status": run.status}
    finally:
        db.close()


def get_latest_failed_adk_run_by_raw_id(
    raw_id: int, org_id: int | None = None, workspace_id: int | None = None
) -> Dict:
    db: Session = SessionLocal()

    try:
        query = db.query(ADKRun).filter(
            ADKRun.raw_id == raw_id, ADKRun.status == "failed"
        )
        query = _apply_org_workspace_filters(query, ADKRun, org_id, workspace_id)
        run = query.order_by(ADKRun.created_at.desc()).first()

        if run is None:
            return {"error": "not_found"}

        return {
            "id": run.id,
            "raw_id": run.raw_id,
            "processed_id": run.processed_id,
            "report_id": run.report_id,
            "error": run.error,
            "error_code": run.error_code,
            "created_at": run.created_at.isoformat(),
            "updated_at": (
                run.updated_at.isoformat() if run.updated_at is not None else None
            ),
            "completed_at": (
                run.completed_at.isoformat() if run.completed_at is not None else None
            ),
            "duration_seconds": _calculate_duration_seconds(
                run.created_at if isinstance(run.created_at, datetime) else None,
                run.completed_at if isinstance(run.completed_at, datetime) else None,
            ),
        }
    finally:
        db.close()


def get_latest_adk_run_by_raw_id(
    raw_id: int, org_id: int | None = None, workspace_id: int | None = None
) -> Dict:
    db: Session = SessionLocal()

    try:
        query = db.query(ADKRun).filter(ADKRun.raw_id == raw_id)
        query = _apply_org_workspace_filters(query, ADKRun, org_id, workspace_id)
        run = query.order_by(ADKRun.created_at.desc()).first()

        if run is None:
            return {"error": "not_found"}

        return {
            "id": run.id,
            "status": run.status,
            "error": run.error,
            "error_code": run.error_code,
            "processed_id": run.processed_id,
            "report_id": run.report_id,
            "created_at": run.created_at.isoformat(),
            "updated_at": (
                run.updated_at.isoformat() if run.updated_at is not None else None
            ),
            "completed_at": (
                run.completed_at.isoformat() if run.completed_at is not None else None
            ),
            "duration_seconds": _calculate_duration_seconds(
                run.created_at if isinstance(run.created_at, datetime) else None,
                run.completed_at if isinstance(run.completed_at, datetime) else None,
            ),
        }

    finally:
        db.close()


def get_adk_run_by_id(
    run_id: int, org_id: int | None = None, workspace_id: int | None = None
) -> Dict:
    db: Session = SessionLocal()

    try:
        query = db.query(ADKRun).filter(ADKRun.id == run_id)
        query = _apply_org_workspace_filters(query, ADKRun, org_id, workspace_id)
        run = query.first()

        if run is None:
            return {"error": "not_found"}

        return {
            "id": run.id,
            "raw_id": run.raw_id,
            "processed_id": run.processed_id,
            "report_id": run.report_id,
            "status": run.status,
            "error": run.error,
            "error_code": run.error_code,
            "created_at": run.created_at.isoformat(),
            "updated_at": (
                run.updated_at.isoformat() if run.updated_at is not None else None
            ),
            "completed_at": (
                run.completed_at.isoformat() if run.completed_at is not None else None
            ),
            "duration_seconds": _calculate_duration_seconds(
                run.created_at if isinstance(run.created_at, datetime) else None,
                run.completed_at if isinstance(run.completed_at, datetime) else None,
            ),
        }

    finally:
        db.close()


def list_adk_runs(
    limit: int = 20, org_id: int | None = None, workspace_id: int | None = None
) -> List[Dict]:
    db: Session = SessionLocal()

    try:
        query = db.query(ADKRun)
        query = _apply_org_workspace_filters(query, ADKRun, org_id, workspace_id)
        runs = query.order_by(ADKRun.created_at.desc()).limit(limit).all()

        return [
            {
                "id": r.id,
                "raw_id": r.raw_id,
                "status": r.status,
                "error": r.error,
                "error_code": r.error_code,
                "processed_id": r.processed_id,
                "report_id": r.report_id,
                "created_at": r.created_at.isoformat(),
                "updated_at": (
                    r.updated_at.isoformat() if r.updated_at is not None else None
                ),
                "completed_at": (
                    r.completed_at.isoformat() if r.completed_at is not None else None
                ),
                "duration_seconds": _calculate_duration_seconds(
                    r.created_at if isinstance(r.created_at, datetime) else None,
                    r.completed_at if isinstance(r.completed_at, datetime) else None,
                ),
            }
            for r in runs
        ]
    finally:
        db.close()


def list_adk_runs_by_raw_id(
    raw_id: int, org_id: int | None = None, workspace_id: int | None = None
) -> List[Dict]:
    db: Session = SessionLocal()

    try:
        query = db.query(ADKRun).filter(ADKRun.raw_id == raw_id)
        query = _apply_org_workspace_filters(query, ADKRun, org_id, workspace_id)
        runs = query.order_by(ADKRun.created_at.desc()).all()

        return [
            {
                "id": r.id,
                "status": r.status,
                "processed_id": r.processed_id,
                "report_id": r.report_id,
                "created_at": r.created_at.isoformat(),
                "updated_at": (
                    r.updated_at.isoformat() if r.updated_at is not None else None
                ),
                "completed_at": (
                    r.completed_at.isoformat() if r.completed_at is not None else None
                ),
                "duration_seconds": _calculate_duration_seconds(
                    r.created_at if isinstance(r.created_at, datetime) else None,
                    r.completed_at if isinstance(r.completed_at, datetime) else None,
                ),
            }
            for r in runs
        ]

    finally:
        db.close()


def get_adk_run_steps(
    run_id: int, org_id: int | None = None, workspace_id: int | None = None
) -> List[Dict]:
    db: Session = SessionLocal()

    try:
        query = db.query(ADKRunStep).filter(ADKRunStep.adk_run_id == run_id)
        if org_id is not None or workspace_id is not None:
            query = query.join(ADKRun, ADKRun.id == ADKRunStep.adk_run_id)
            query = _apply_org_workspace_filters(query, ADKRun, org_id, workspace_id)
        steps = query.order_by(ADKRunStep.id.asc()).all()

        return [
            {
                "id": s.id,
                "step": s.step,
                "status": s.status,
                "data": s.data,
                "error": s.error,
                "error_code": s.error_code,
                "created_at": (
                    s.created_at.isoformat() if s.created_at is not None else None
                ),
                "finished_at": (
                    s.finished_at.isoformat() if s.finished_at is not None else None
                ),
                "duration_seconds": _calculate_duration_seconds(
                    s.created_at if isinstance(s.created_at, datetime) else None,
                    s.finished_at if isinstance(s.finished_at, datetime) else None,
                ),
            }
            for s in steps
        ]
    finally:
        db.close()


# ============Write Ops==============


def create_processed_data(
    raw_id: int,
    structured: Any,
    org_id: int | None = None,
    workspace_id: int | None = None,
) -> Dict:
    db: Session = SessionLocal()

    try:
        if org_id is None or workspace_id is None:
            org_workspace = _get_org_workspace_for_raw(db, raw_id)
            if org_workspace is None:
                return {"error": "raw_data not found"}
            org_id, workspace_id = org_workspace

        # Ensure raw_id is included in structured JSON
        if isinstance(structured, dict):
            # Always include raw_id, overwriting if it exists to ensure consistency
            structured_with_raw = {"raw_id": raw_id, **structured}
            structured = structured_with_raw
        else:
            # If structured is not a dict, wrap it
            structured = {"raw_id": raw_id, "structured": structured}

        p = ProcessedData(
            org_id=org_id,
            workspace_id=workspace_id,
            structured=structured,
        )

        db.add(p)
        db.commit()
        db.refresh(p)
        return {"id": p.id, "raw_id": raw_id}

    finally:
        db.close()


def create_policy_rule(
    name: str,
    description: str | None,
    severity: str,
    category: str,
    pattern_type: str,
    pattern: str | None,
    scope: Any | None,
    remediation: str | None,
    is_active: bool,
    org_id: int,
    workspace_id: int,
    actor: str | None = None,
) -> Dict:
    db: Session = SessionLocal()
    try:
        rule = PolicyRule(
            org_id=org_id,
            workspace_id=workspace_id,
            name=name,
            description=description,
            severity=severity,
            category=category,
            pattern_type=pattern_type,
            pattern=pattern,
            scope=scope,
            remediation=remediation,
            version="v1",
            is_active=1 if is_active else 0,
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
            "is_active": bool(rule.is_active),
        }

        version = PolicyRuleVersion(
            rule_id=rule.id,
            version=rule.version,
            content_snapshot=snapshot,
            created_at=datetime.now(timezone.utc),
        )
        audit = PolicyRuleAudit(
            rule_id=rule.id,
            action="created",
            actor=actor,
            changes=snapshot,
            created_at=datetime.now(timezone.utc),
        )
        db.add_all([version, audit])
        db.commit()

        return {"id": rule.id, "version": rule.version}
    finally:
        db.close()


def update_policy_rule(
    rule_id: int,
    updates: Dict[str, Any],
    org_id: int | None = None,
    workspace_id: int | None = None,
    actor: str | None = None,
) -> Dict:
    db: Session = SessionLocal()
    try:
        query = db.query(PolicyRule).filter(PolicyRule.id == rule_id)
        query = _apply_org_workspace_filters(query, PolicyRule, org_id, workspace_id)
        rule = query.first()
        if rule is None:
            return {"error": "not_found"}

        previous = {
            "name": rule.name,
            "description": rule.description,
            "severity": rule.severity,
            "category": rule.category,
            "pattern_type": rule.pattern_type,
            "pattern": rule.pattern,
            "scope": rule.scope,
            "remediation": rule.remediation,
            "version": rule.version,
            "is_active": bool(rule.is_active),
        }

        for key, value in updates.items():
            if key == "is_active":
                setattr(rule, key, 1 if value else 0)
            else:
                setattr(rule, key, value)

        next_version_number = int(rule.version.lstrip("v") or "1") + 1
        rule.version = f"v{next_version_number}"
        rule.updated_at = datetime.now(timezone.utc)

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
            "is_active": bool(rule.is_active),
        }

        version = PolicyRuleVersion(
            rule_id=rule.id,
            version=rule.version,
            content_snapshot=snapshot,
            created_at=datetime.now(timezone.utc),
        )
        audit = PolicyRuleAudit(
            rule_id=rule.id,
            action="updated",
            actor=actor,
            changes={"before": previous, "after": snapshot},
            created_at=datetime.now(timezone.utc),
        )

        db.add_all([version, audit])
        db.commit()
        db.refresh(rule)

        return {"id": rule.id, "version": rule.version}
    finally:
        db.close()


def deactivate_policy_rule(
    rule_id: int,
    actor: str | None = None,
    org_id: int | None = None,
    workspace_id: int | None = None,
) -> Dict:
    db: Session = SessionLocal()
    try:
        query = db.query(PolicyRule).filter(PolicyRule.id == rule_id)
        query = _apply_org_workspace_filters(query, PolicyRule, org_id, workspace_id)
        rule = query.first()
        if rule is None:
            return {"error": "not_found"}

        rule.is_active = 0
        rule.updated_at = datetime.now(timezone.utc)

        audit = PolicyRuleAudit(
            rule_id=rule.id,
            action="deactivated",
            actor=actor,
            changes={"is_active": False},
            created_at=datetime.now(timezone.utc),
        )
        db.add(audit)
        db.commit()

        return {"id": rule.id, "is_active": False}
    finally:
        db.close()


def create_violation(
    processed_id: int,
    rule: str,
    severity: str,
    details: Any,
    org_id: int | None = None,
    workspace_id: int | None = None,
) -> Dict:

    db: Session = SessionLocal()

    try:
        if org_id is None or workspace_id is None:
            org_workspace = _get_org_workspace_for_processed(db, processed_id)
            if org_workspace is None:
                return {"error": "processed_data not found"}
            org_id, workspace_id = org_workspace

        v = Violation(
            org_id=org_id,
            workspace_id=workspace_id,
            rule=rule,
            severity=severity,
            details={"processed_id": processed_id, **details},
            created_at=datetime.now(timezone.utc),
        )
        db.add(v)
        db.commit()
        db.refresh(v)
        return {"id": v.id, "processed_id": processed_id}
    finally:
        db.close()


def create_report(
    processed_id: int,
    score: int,
    summary: str,
    content: Any,
    org_id: int | None = None,
    workspace_id: int | None = None,
) -> Dict:
    db: Session = SessionLocal()

    try:
        if org_id is None or workspace_id is None:
            org_workspace = _get_org_workspace_for_processed(db, processed_id)
            if org_workspace is None:
                return {"error": "processed_data not found"}
            org_id, workspace_id = org_workspace

        report = Report(
            org_id=org_id,
            workspace_id=workspace_id,
            score=score,
            summary=summary,
            content=content,
            created_at=datetime.now(timezone.utc),
        )

        db.add(report)
        db.commit()
        db.refresh(report)

        return {"id": report.id, "processed_id": processed_id, "score": score}

    finally:
        db.close()


def update_report(report_id: int, summary: str, content: Any, score: int) -> Dict:
    db: Session = SessionLocal()

    try:
        r = db.query(Report).filter(Report.id == report_id).first()

        if r is None:
            return {"error": "not_found"}

        setattr(r, "summary", summary)
        setattr(r, "content", content)
        setattr(r, "score", score)
        setattr(r, "updated_at", datetime.now(timezone.utc))

        db.commit()
        db.refresh(r)

        return {"id": r.id, "summary": r.summary, "score": r.score}
    finally:
        db.close()


def log_agent_action(agent_name: str, action: str, details: Any) -> Dict:

    db: Session = SessionLocal()

    try:
        log = AgentLog(
            agent_name=agent_name,
            action=action,
            details=details,
            created_at=datetime.now(timezone.utc),
        )
        db.add(log)
        db.commit()
        db.refresh(log)
        return {"id": log.id}
    finally:
        db.close()


def create_adk_run(
    raw_id: int,
    status: str,
    org_id: int | None = None,
    workspace_id: int | None = None,
) -> Dict:
    db: Session = SessionLocal()

    try:
        if org_id is None or workspace_id is None:
            org_workspace = _get_org_workspace_for_raw(db, raw_id)
            if org_workspace is None:
                return {"error": "raw_data not found"}
            org_id, workspace_id = org_workspace

        run = ADKRun(
            raw_id=raw_id,
            status=status,
            org_id=org_id,
            workspace_id=workspace_id,
            created_at=datetime.now(timezone.utc),
        )
        db.add(run)
        db.commit()
        db.refresh(run)

        return {"id": run.id}
    finally:
        db.close()


def update_adk_run(
    run_id: int,
    status: str,
    processed_id: int | None = None,
    report_id: int | None = None,
    error: str | None = None,
    error_code: str | None = None,
) -> Dict:
    db: Session = SessionLocal()

    try:
        adk = db.query(ADKRun).filter(ADKRun.id == run_id).first()

        if adk is None:
            return {"error": "not_found"}

        if processed_id is not None:
            setattr(adk, "processed_id", processed_id)
        if report_id is not None:
            setattr(adk, "report_id", report_id)
        if error is not None:
            setattr(adk, "error", error)
        if error_code is not None:
            setattr(adk, "error_code", error_code)
        setattr(adk, "status", status)
        setattr(adk, "updated_at", datetime.now(timezone.utc))

        if status in ("completed", "failed"):
            setattr(adk, "completed_at", datetime.now(timezone.utc))

        db.commit()
        db.refresh(adk)

        return {
            "id": adk.id,
            "status": adk.status,
            "processed_id": adk.processed_id,
            "report_id": adk.report_id,
            "error": adk.error,
            "error_code": adk.error_code,
        }
    finally:
        db.close()


def create_adk_run_step(
    run_id: int,
    step: str,
    status: str,
    data: Any | None = None,
    error: str | None = None,
    error_code: str | None = None,
) -> Dict:
    if run_id is None:
        return {"error": "run_id is required"}

    db: Session = SessionLocal()

    try:
        finished_at = None
        if status in ("success", "failed", "skipped"):
            finished_at = datetime.now(timezone.utc)

        s = ADKRunStep(
            adk_run_id=run_id,
            step=step,
            status=status,
            data=data,
            error=error,
            error_code=error_code,
            created_at=datetime.now(timezone.utc),
            finished_at=finished_at,
        )

        db.add(s)
        db.commit()
        db.refresh(s)

        return {"id": s.id}
    finally:
        db.close()


def finish_adk_run_step(step_id: int) -> Dict:
    db: Session = SessionLocal()
    try:
        step = db.query(ADKRunStep).filter(ADKRunStep.id == step_id).first()
        if step is None:
            return {"error": "not_found"}

        setattr(step, "finished_at", datetime.now(timezone.utc))
        db.commit()
        return {"id": step.id}

    finally:
        db.close()
