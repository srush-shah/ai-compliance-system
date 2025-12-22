"""
ADK Report Writer Agent

Responsible for generating final structured report content
based on violations and existing report metadata.
"""

from typing import Any, Dict

from adk.tools.tools_registry import get_adk_tools


class ReportWriterADKAgent:
    def __init__(self):
        self.name = "Report Writer"
        self.tools = get_adk_tools()

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

        # 4. Build structured content
        content = {
            "report_id": report_id,
            "processed_id": processed_id,
            "violation_count": violation_count,
            "violations": violations,
            "generated_by": self.name,
        }

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

    def run(self, report_id: int) -> Dict[str, Any]:
        report = self.tools["get_report_by_id"](report_id)
        processed_id = report["content"]["processed_id"]

        return self.write_report(report_id=report_id, processed_id=processed_id)
