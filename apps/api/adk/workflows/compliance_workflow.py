"""
Compliance Review Workflow (ADK-style orchestration).

This module coordinates ADK agents in a fixed sequence.
"""

from adk.agents.compliance_checker_agent import ComplianceCheckerADKAgent
from adk.agents.data_engineer_agent import DataEngineerADKAgent
from adk.agents.report_writer_agent import ReportWriterADKAgent
from adk.agents.risk_assessor_agent import RiskAssessorADKAgent


class ComplianceReviewWorkflow:
    def __init__(self):
        self.data_engineer = DataEngineerADKAgent()
        self.compliance_checker = ComplianceCheckerADKAgent()
        self.risk_assessor = RiskAssessorADKAgent()
        self.report_writer = ReportWriterADKAgent()

    def run(self, raw_id: int) -> dict:
        """
        Orchestrates the full compliance workflow.

        Input:
            raw_id: ID of raw uploaded data

        Output:
            dict with final report_id and status
        """

        raise NotImplementedError("Workflow logic not implemented yet.")
