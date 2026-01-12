"""
ADK Compliance Checker Agent

Fetches processed data, checks against policy rules, creates violations, and logs actions via ADK tools.
"""

from typing import Dict, List

from adk.tools.tools_registry import get_adk_tools
from services.rule_engine import evaluate_rules


class ComplianceCheckerADKAgent:
    def __init__(self):
        self.name = "Compliance Checker"
        self.tools = get_adk_tools()

    def check_compliance(self, processed_id: int) -> Dict:
        """
        Run compliance check on processed data.
        Steps:
        1. Fetch processed data
        2. Fetch policy rules
        3. Apply rules to detect violations
        4. Create violation entries
        5. Log actions
        """
        # 1. Fetch processed data
        processed = self.tools["get_processed_data_by_id"](processed_id)

        if "error" in processed:
            return {"error": "processed_data not found", "processed_id": processed_id}

        # 2. Fetch policy rules
        rules = self.tools["get_policy_rules"]()

        if not rules or "error" in rules:
            return {"error": "policy_rules not found"}

        violations_created: List[Dict] = []

        # 3. Apply rules across normalized sections
        structured = processed.get("structured", {})
        sections = structured.get("sections", [])

        if not sections:
            fallback_text = str(structured.get("full_content") or structured.get("raw_content") or "")
            sections = [{"chunk_id": None, "label": "raw", "text": fallback_text}]

        detected = evaluate_rules(rules, sections)

        for match in detected:
            violation = self.tools["create_violation"](
                processed_id=processed_id,
                rule=match.get("rule") or "unknown",
                severity=match.get("severity") or "medium",
                details={
                    "rule_id": match.get("rule_id"),
                    "evidence": match.get("evidence"),
                    "location": match.get("location"),
                    "confidence": match.get("confidence"),
                    "recommended_fix": match.get("recommended_fix"),
                },
            )
            violations_created.append(violation)

        # 5. Log Action
        self.tools["log_agent_action"](
            agent_name=self.name,
            action="checked_compliance",
            details={
                "processed_id": processed_id,
                "violations_count": len(violations_created),
            },
        )

        return {"processed_id": processed_id, "violations": violations_created}

    def run(self, processed_id: int) -> Dict:
        return self.check_compliance(processed_id=processed_id)
