"""
ADK Compliance Checker Agent

Fetches processed data, checks against policy rules, creates violations, and logs actions via ADK tools.
"""

from typing import Dict, List

from adk.tools.tools_registry import get_adk_tools


class ComplianceCheckerADKAgent:
    def __init__(self):
        self.name = "Compliance Checker"
        self.tools = get_adk_tools()

    def describe(self):
        """
        Debug helper to verify wiring.
        """

        return {"agent": self.name, "available_tools": list(self.tools.keys())}

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

        # 3. Apply rules (simple substring matching for now)
        # Extract text content from structured data
        full_content = processed["structured"].get("full_content", "")
        # Handle both string and dict content
        if isinstance(full_content, dict):
            content_text = str(full_content.get("raw_text", full_content))
        else:
            content_text = str(full_content)

        for rule in rules:
            if rule["name"].lower() in content_text.lower():

                # 4. Create violation
                violation = self.tools["create_violation"](
                    processed_id=processed_id,
                    rule=rule["name"],
                    severity=rule["severity"],
                    details={"matched_text": rule["name"]},
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
