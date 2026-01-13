"""
ADK Report Writer Agent

Responsible for generating final structured report content
based on violations and existing report metadata.
"""

import json
from typing import Any, Dict, List

from adk.tools.tools_registry import get_adk_tools


class ReportWriterADKAgent:
    def __init__(self):
        self.name = "Report Writer"
        self.tools = get_adk_tools()

    def _build_violation_rows(self, violations: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        rows = []
        for v in violations:
            details = v.get("details")
            if isinstance(details, dict):
                detail_text = (
                    details.get("message")
                    or details.get("description")
                    or json.dumps(details)
                )
            elif details is None:
                detail_text = ""
            else:
                detail_text = str(details)

            rows.append(
                {
                    "id": v.get("id"),
                    "rule": v.get("rule"),
                    "severity": v.get("severity"),
                    "details": detail_text,
                    "created_at": v.get("created_at"),
                }
            )
        return rows

    def _build_top_risks(self, violations: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        severity_rank = {"critical": 4, "high": 3, "medium": 2, "low": 1}
        severity_counts: Dict[str, int] = {}
        rules_by_severity: Dict[str, Dict[str, int]] = {}

        for violation in violations:
            severity = (violation.get("severity") or "unknown").lower()
            rule = violation.get("rule") or "unknown"
            severity_counts[severity] = severity_counts.get(severity, 0) + 1
            rules_by_severity.setdefault(severity, {})
            rules_by_severity[severity][rule] = (
                rules_by_severity[severity].get(rule, 0) + 1
            )

        top_risks = []
        for severity, count in severity_counts.items():
            rules = rules_by_severity.get(severity, {})
            top_rules = sorted(rules.items(), key=lambda item: item[1], reverse=True)[:3]
            top_risks.append(
                {
                    "severity": severity,
                    "count": count,
                    "top_rules": [
                        {"rule": rule, "count": rule_count}
                        for rule, rule_count in top_rules
                    ],
                }
            )

        return sorted(
            top_risks,
            key=lambda item: (severity_rank.get(item["severity"], 0), item["count"]),
            reverse=True,
        )

    def _build_remediation_plan(
        self, violations: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        plan: Dict[str, Dict[str, Any]] = {}
        for violation in violations:
            rule = violation.get("rule") or "unknown"
            if rule not in plan:
                plan[rule] = {
                    "rule": rule,
                    "severity": violation.get("severity"),
                    "recommendation": (
                        f"Review policy expectations for {rule} and remediate any "
                        "detected issues in the source data."
                    ),
                }

        return list(plan.values())

    def _build_audit_excerpt(
        self, violations: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        entries = []
        for violation in violations[-5:]:
            rule = violation.get("rule") or "unknown"
            severity = violation.get("severity") or "unknown"
            entries.append(
                {
                    "timestamp": violation.get("created_at"),
                    "event": f"Violation logged for {rule} ({severity}).",
                }
            )
        return entries

    def write_report(self, report_id: int, processed_id: int) -> Dict[str, Any]:
        """
        Generate and persist final report content.
        """

        # 1. Fetch existing report
        report = self.tools["get_report_by_id"](report_id)
        if "error" in report:
            return {"error": "report not found"}

        # 2. Fetch violations for this processed data
        violations = self.tools["get_violations_by_processed_id"](processed_id)

        # 3. Build summary
        violation_count = len(violations)
        summary = (
            f"Compliance review completed. " f"{violation_count} violation(s) detected."
        )

        violations_table = self._build_violation_rows(violations)
        top_risks = self._build_top_risks(violations)
        remediation_plan = self._build_remediation_plan(violations)
        audit_excerpt = self._build_audit_excerpt(violations)

        # 4. Build structured content
        existing_content = report.get("content") if isinstance(report, dict) else None
        content = {
            "report_id": report_id,
            "processed_id": processed_id,
            "violation_count": violation_count,
            "violations": violations,
            "violations_table": violations_table,
            "executive_summary": summary,
            "top_risks": top_risks,
            "remediation_plan": remediation_plan,
            "audit_excerpt": audit_excerpt,
            "generated_by": self.name,
        }
        if isinstance(existing_content, dict):
            content = {**existing_content, **content}

        # 5. Persist report update
        # Get existing score from report, calculate if not present
        score = (
            report.get("score")
            if report.get("score") is not None
            else min(violation_count * 10, 100)
        )
        self.tools["update_report"](
            report_id=report_id, summary=summary, content=content, score=score
        )

        # 6. Log agent action
        self.tools["log_agent_action"](
            agent_name=self.name,
            action="write_report",
            details={
                "report_id": report_id,
                "processed_id": processed_id,
                "violation_count": violation_count,
            },
        )

        return {
            "status": "success",
            "report_id": report_id,
            "violation_count": violation_count,
        }

    def run(self, report_id: int, processed_id: int) -> Dict[str, Any]:
        return self.write_report(report_id=report_id, processed_id=processed_id)
