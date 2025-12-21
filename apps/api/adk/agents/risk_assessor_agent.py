"""
ADK Risk Assessor Agent

Calculates risk score based on violaitons
and generates a report entry.
"""

from typing import Dict, List

from adk.tools.tools_registry import get_adk_tools


class RiskAssessorADKAgent:
    def __init__(self):
        self.name = "Risk Assessor"
        self.tools = get_adk_tools()

    def describe(self):
        return {"agent": self.name, "available_tools": list(self.tools.keys())}

    def assess_risk(self, processed_id: int) -> Dict:
        # 1. Fetch violations
        violations = self.tools["get_violations_by_processed_id"](processed_id)

        if violations is None:
            return {"error": "violations fetch failed"}

        # 2. Compute risk score
        # Simple rule: 10 points per violation, capped at 100
        score = min(len(violations) * 10, 100)

        summary = f"Risk Score: {score}. Total Violations: {len(violations)}."

        content = {
            "processed_id": processed_id,
            "violation_count": len(violations),
            "violations": violations,
            "risk_score": score,
        }

        # 4. Create report
        report = self.tools["create_report"](
            processed_id=processed_id, score=score, summary=summary, content=content
        )

        # 5. Log Action
        self.tools["log_agent_action"](
            agent_name=self.name,
            action="assessed_risk",
            details={
                "processed_id": processed_id,
                "score": score,
                "report_id": report["id"],
            },
        )

        return {"processed_id": processed_id, "report_id": report["id"], "score": score}
