"""
ADK Compliance Checker Agent (tool-aware, non-executing).
"""

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
