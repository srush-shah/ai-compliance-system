import csv
import io
import json

from db import SessionLocal
from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from models import Report

router = APIRouter(prefix="/reports", tags=["reports"])


def _stringify_details(details: object) -> str:
    if details is None:
        return ""
    if isinstance(details, (dict, list)):
        return json.dumps(details)
    return str(details)


@router.get("/{report_id}.json")
def get_report_json(report_id: int):
    db = SessionLocal()
    try:
        report = db.query(Report).filter(Report.id == report_id).first()
        if report is None:
            raise HTTPException(status_code=404, detail="report not found")

        if report.content:
            return report.content

        return {
            "report_id": report.id,
            "summary": report.summary,
            "score": report.score,
            "created_at": (
                report.created_at.isoformat() if report.created_at is not None else None
            ),
        }
    finally:
        db.close()


@router.get("/{report_id}/violations.csv")
def export_report_violations_csv(report_id: int):
    db = SessionLocal()
    try:
        report = db.query(Report).filter(Report.id == report_id).first()
        if report is None:
            raise HTTPException(status_code=404, detail="report not found")

        content = report.content or {}
        violations = content.get("violations_table") or content.get("violations") or []

        output = io.StringIO()
        fieldnames = ["id", "rule", "severity", "details", "created_at"]
        writer = csv.DictWriter(output, fieldnames=fieldnames)
        writer.writeheader()
        for violation in violations:
            if not isinstance(violation, dict):
                continue
            writer.writerow(
                {
                    "id": violation.get("id"),
                    "rule": violation.get("rule"),
                    "severity": violation.get("severity"),
                    "details": _stringify_details(violation.get("details")),
                    "created_at": violation.get("created_at"),
                }
            )

        response = StreamingResponse(iter([output.getvalue()]), media_type="text/csv")
        response.headers["Content-Disposition"] = (
            f'attachment; filename="report-{report_id}-violations.csv"'
        )
        return response
    finally:
        db.close()


@router.get("/{report_id}.pdf")
def export_report_pdf(report_id: int):
    db = SessionLocal()
    try:
        report = db.query(Report).filter(Report.id == report_id).first()
        if report is None:
            raise HTTPException(status_code=404, detail="report not found")
    finally:
        db.close()

    raise HTTPException(status_code=501, detail="PDF export not implemented")
