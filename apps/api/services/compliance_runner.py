from adk.tools.tools_registry import get_adk_tools
from adk.workflows.compliance_workflow import ComplianceReviewWorkflow


def run_compliance_workflow(raw_id: int, run_id: int, is_retry: bool):
    workflow = ComplianceReviewWorkflow()
    try:
        workflow.run(raw_id=raw_id, run_id=run_id, is_retry=is_retry)
    except Exception as e:
        tools = get_adk_tools()
        tools["update_adk_run"](run_id=run_id, status="failed", error=str(e))
        raise
