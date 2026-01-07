import asyncio

from adk.tools.tools_registry import get_adk_tools
from google_adk.runner import run_google_adk_compliance

# from adk.workflows.compliance_workflow import ComplianceReviewWorkflow

tools = get_adk_tools()


def run_compliance_workflow(raw_id: int, run_id: int, is_retry: bool) -> None:
    """
    Background task entrypoint for running the Google ADK compliance workflow.

    This is a synchronous function (required by FastAPI BackgroundTasks) that
    internally runs the async ADK runner using its own event loop.
    """

    # Mark step as started
    tools["create_adk_run_step"](
        run_id=run_id, step="google_adk", status="started", data={"status": "started"}
    )

    # Run the async ADK workflow in this background thread
    result = asyncio.run(
        run_google_adk_compliance(raw_id=raw_id, session_id=f"run-{run_id}")
    )

    error = result.get("error") if isinstance(result, dict) else None

    if error:
        tools["create_adk_run_step"](
            run_id=run_id,
            step="google_adk",
            status="failed",
            error=error,
        )
        tools["update_adk_run"](run_id=run_id, status="failed", error=str(error))
        return

    tools["update_adk_run"](
        run_id=run_id,
        status="completed",
        processed_id=result.get("processed_id") if isinstance(result, dict) else None,
        report_id=result.get("report_id") if isinstance(result, dict) else None,
        error=None,
    )


# def run_compliance_workflow(raw_id: int, run_id: int, is_retry: bool):
#     workflow = ComplianceReviewWorkflow()
#     try:
#         workflow.run(raw_id=raw_id, run_id=run_id, is_retry=is_retry)
#     except Exception as e:
#         tools = get_adk_tools()
#         tools["update_adk_run"](run_id=run_id, status="failed", error=str(e))
#         raise
#         raise
