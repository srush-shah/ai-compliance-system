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
        if "error" in data_result:
            return {
                "status": "failed",
                "error": data_result.get("error"),
                "step": "data_engineering",
            }
        processed_id = data_result["processed_id"]

        # 2. Compliance checking
        compliance_result = self.compliance_checker.run(processed_id=processed_id)
        if "error" in compliance_result:
            return {
                "status": "failed",
                "error": compliance_result.get("error"),
                "step": "compliance_checking",
            }

        # 3. Risk assesssment
        risk_result = self.risk_assessor.run(processed_id=processed_id)
        if "error" in risk_result:
            return {
                "status": "failed",
                "error": risk_result.get("error"),
                "step": "risk_assessment",
            }
        report_id = risk_result["report_id"]

        # 4. Report writing
        report_result = self.report_writer.run(report_id=report_id)
        if "error" in report_result:
            return {
                "status": "failed",
                "error": report_result.get("error"),
                "step": "report_writing",
            }

        return {"status": "completed", "report_id": report_id}
