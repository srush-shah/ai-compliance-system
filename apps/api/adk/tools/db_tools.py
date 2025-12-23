from datetime import datetime, timezone
from typing import Dict, List

from db import SessionLocal
from models import (
    ADKRun,
    AgentLog,
    PolicyRule,
    ProcessedData,
    RawData,
    Report,
    Violation,
)
from sqlalchemy import Integer, cast, text
from sqlalchemy.orm import Session

# =========Read Ops==================


def get_raw_data_by_id(raw_id: int) -> Dict:
    db: Session = SessionLocal()

    try:
        r = db.query(RawData).filter(RawData.id == raw_id).first()

        if r is None:
            return {"error": "not_found"}

        return {
            "id": r.id,
            "content": r.content,
            "created_at": r.created_at.isoformat() if r.created_at else None,
        }
    finally:
        db.close()


def get_processed_data_by_id(processed_id: int) -> Dict:
    db: Session = SessionLocal()

    try:
        p = db.query(ProcessedData).filter(ProcessedData.id == processed_id).first()

        if p is None:
            return {"error": "not_found"}

        return {
            "id": p.id,
            "structured": p.structured,
            "created_at": p.created_at.isoformat() if p.created_at else None,
        }
    finally:
        db.close()


def get_policy_rules() -> List[Dict]:
    db: Session = SessionLocal()

    try:
        rules = db.query(PolicyRule).all()

        if rules is None:
            return {"error": "no policies found"}

        return [
            {
                "id": r.id,
                "name": r.name,
                "description": r.description,
                "severity": r.severity,
            }
            for r in rules
        ]
    finally:
        db.close()


def get_violations_by_processed_id(processed_id: int) -> List[Dict]:
    db: Session = SessionLocal()

    try:
        violations = (
            db.query(Violation)
            .filter(
                cast(text("violations.details ->> 'processed_id'"), Integer)
                == processed_id
            )
            .all()
        )

        return [
            {
                "id": v.id,
                "rule": v.rule,
                "severity": v.severity,
                "details": v.details,
                "created_at": v.created_at.isoformat() if v.created_at else None,
            }
            for v in violations
        ]
    finally:
        db.close()


def get_report_by_id(report_id: int) -> Dict:
    db: Session = SessionLocal()
    try:
        r = db.query(Report).filter(Report.id == report_id).first()
        if not r:
            return {"error": "not found"}

        return {
            "id": r.id,
            "summary": r.summary,
            "score": r.score,
            "content": r.content,
            "created_at": r.created_at.isoformat() if r.created_at else None,
        }

    finally:
        db.close()


# ============Write Ops==============


def create_processed_data(raw_id: int, structured: Dict) -> Dict:
    db: Session = SessionLocal()

    try:
        p = ProcessedData(structured=structured)

        db.add(p)
        db.commit()
        db.refresh(p)
        return {"id": p.id, "raw_id": raw_id}

    finally:
        db.close()


def create_violation(
    processed_id: int, rule: str, severity: str, details: Dict
) -> Dict:

    db: Session = SessionLocal()

    try:
        v = Violation(
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


def create_report(processed_id: int, score: int, summary: str, content: Dict) -> Dict:
    db: Session = SessionLocal()

    try:
        report = Report(
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


def update_report(report_id: int, summary: str, content: Dict, score: int) -> Dict:
    db: Session = SessionLocal()

    try:
        r = db.query(Report).filter(Report.id == report_id).first()

        if r is None:
            return {"error": "not_found"}

        r.summary = summary
        r.content = content
        r.score = score
        r.created_at = datetime.now(timezone.utc)

        db.commit()
        db.refresh(r)

        return {"id": r.id, "summary": r.summary, "score": r.score}
    finally:
        db.close()


def log_agent_action(agent_name: str, action: str, details: Dict) -> Dict:

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


def create_adk_run(raw_id: int, status: str) -> Dict:
    db: Session = SessionLocal()

    try:
        run = ADKRun(
            raw_id=raw_id, status=status, created_at=datetime.now(timezone.utc)
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
) -> Dict:
    db: Session = SessionLocal()

    try:
        adk = db.query(ADKRun).filter(ADKRun.id == run_id).first()

        if adk is None:
            return {"error": "not_found"}

        adk.processed_id = processed_id
        adk.report_id = report_id
        adk.error = error
        adk.status = status
        adk.updated_at = datetime.now(timezone.utc)

        db.commit()
        db.refresh(adk)

        return {
            "id": adk.id,
            "status": adk.status,
            "processed_id": adk.processed_id,
            "report_id": adk.report_id,
            "error": adk.error,
        }
    finally:
        db.close()
