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
        # 1. Data engineering
        data_result = self.data_engineer.run(raw_id=raw_id)
        processed_id = data_result["processed_id"]

        # 2. Compliance checking
        compliance_result = self.compliance_checker.run(processed_id=processed_id)

        # 3. Risk assesssment
        risk_result = self.risk_assessor.run(processed_id=processed_id)
        report_id = risk_result["report_id"]

        # 4. Report writing
        self.report_writer.run(report_id=report_id)

        return {"status": "completed", "report_id": report_id}
