"""
Compliance Review Workflow (ADK-style orchestration).

This module coordinates ADK agents in a fixed sequence.
"""

from adk.agents.compliance_checker_agent import ComplianceCheckerADKAgent
from adk.agents.data_engineer_agent import DataEngineerADKAgent
from adk.agents.report_writer_agent import ReportWriterADKAgent
from adk.agents.risk_assessor_agent import RiskAssessorADKAgent
from adk.tools.tools_registry import get_adk_tools
from adk.workflows.types import WorkflowResult, WorkflowStepResult
from fastapi import HTTPException


class ComplianceReviewWorkflow:
    def __init__(self):
        self.data_engineer = DataEngineerADKAgent()
        self.compliance_checker = ComplianceCheckerADKAgent()
        self.risk_assessor = RiskAssessorADKAgent()
        self.report_writer = ReportWriterADKAgent()
        self.tools = get_adk_tools()

    def run(self, raw_id: int) -> dict:
        active = self.tools["get_active_adk_run_by_raw_id"](raw_id)
        if active.get("active"):
            return {"status": "already_running", "run_id": active["run_id"]}

        failed = self.tools["get_latest_failed_adk_run_by_raw_id"](raw_id)
        retry_processed_id = None

        if "error" not in failed:
            retry_processed_id = failed.get("processed_id")

        adk_run = self.tools["create_adk_run"](raw_id=raw_id, status="started")
        adk_run_id = adk_run["id"]

        steps = {}

        # 1. Data engineering
        if retry_processed_id:
            processed_id = retry_processed_id
            steps["data_engineering"] = WorkflowStepResult(
                step="data_engineering",
                status="skipped",
                data={"processed_id": processed_id, "reason": "retry_reuse"},
            )

        else:
            data_result = self.data_engineer.run(raw_id=raw_id)

            if "error" in data_result:
                steps["data_engineering"] = WorkflowStepResult(
                    step="data_engineering", status="failed", error=data_result["error"]
                )

                self.tools["update_adk_run"](
                    run_id=adk_run_id, status="failed", error="data engineering failed"
                )
                return WorkflowResult(
                    status="failed", raw_id=raw_id, steps=steps
                ).model_dump()

            processed_id = data_result["processed_id"]
            steps["data_engineering"] = WorkflowStepResult(
                step="data_engineering", status="success", data=data_result
            )

        # 2. Compliance checking
        compliance_result = self.compliance_checker.run(processed_id=processed_id)
        if "error" in compliance_result:
            steps["compliance_checking"] = WorkflowStepResult(
                step="compliance_checking",
                status="failed",
                error=compliance_result["error"],
            )

            self.tools["update_adk_run"](
                run_id=adk_run_id, status="failed", error="compliance check failed"
            )
            return WorkflowResult(
                status="failed", raw_id=raw_id, processed_id=processed_id, steps=steps
            ).model_dump()

        steps["compliance_checking"] = WorkflowStepResult(
            step="compliance_checking", status="success", data=compliance_result
        )

        # 3. Risk assesssment
        risk_result = self.risk_assessor.run(processed_id=processed_id)
        if "error" in risk_result:
            steps["risk_assessment"] = WorkflowStepResult(
                step="risk_assessment", status="failed", error=risk_result["error"]
            )

            self.tools["update_adk_run"](
                run_id=adk_run_id, status="failed", error="risk assessment failed"
            )

            return WorkflowResult(
                status="failed", raw_id=raw_id, processed_id=processed_id, steps=steps
            ).model_dump()

        report_id = risk_result["report_id"]
        steps["risk_assessment"] = WorkflowStepResult(
            step="risk_assessment", status="success", data=risk_result
        )

        # 4. Report writing
        report_result = self.report_writer.run(report_id=report_id)
        if "error" in report_result:
            steps["report_writing"] = WorkflowStepResult(
                step="report_writing", status="failed", error=report_result["error"]
            )

            self.tools["update_adk_run"](
                run_id=adk_run_id, status="failed", error="report writing failed"
            )

            return WorkflowResult(
                status="failed",
                raw_id=raw_id,
                processed_id=processed_id,
                report_id=report_id,
                steps=steps,
            ).model_dump()

        steps["report_writing"] = WorkflowStepResult(
            step="report_writing", status="success", data=report_result
        )

        self.tools["update_adk_run"](
            run_id=adk_run_id,
            processed_id=processed_id,
            report_id=report_id,
            status="completed",
        )
        return WorkflowResult(
            status="completed",
            raw_id=raw_id,
            processed_id=processed_id,
            report_id=report_id,
            steps=steps,
        ).model_dump()

    def retry(self, raw_id: int) -> dict:
        latest = self.tools["get_latest_adk_run_by_raw_id"](raw_id)

        if "id" not in latest and "error" in latest:
            raise HTTPException(status_code=404, detail="No previous run found")

        if latest["status"] != "failed":
            return {
                "status": "not_allowed",
                "messsage": "Only failed runs can be retried",
                "run_id": latest["id"],
            }

        return self.run(raw_id=raw_id)
