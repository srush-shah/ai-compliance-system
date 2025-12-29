from adk.workflows.compliance_workflow import ComplianceReviewWorkflow


def run_compliance_workflow(raw_id: int, run_id: int, is_retry: bool):
    workflow = ComplianceReviewWorkflow()
    workflow.run(raw_id=raw_id, run_id=run_id, is_retry=is_retry)
