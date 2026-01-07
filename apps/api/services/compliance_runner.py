import asyncio

from adk.tools.tools_registry import get_adk_tools
from adk.workflows.compliance_workflow import ComplianceReviewWorkflow
from google_adk.runner import run_google_adk_compliance

tools = get_adk_tools()


def _is_rate_limit_error(error: Exception) -> bool:
    """Check if error is a Google ADK rate limit (429) error."""
    error_str = str(error)
    return (
        "429" in error_str
        or "RESOURCE_EXHAUSTED" in error_str
        or "quota" in error_str.lower()
        or "rate limit" in error_str.lower()
    )


def _run_manual_workflow(raw_id: int, run_id: int, is_retry: bool) -> dict:
    """Fallback to manual workflow when Google ADK fails."""
    workflow = ComplianceReviewWorkflow()
    return workflow.run(raw_id=raw_id, run_id=run_id, is_retry=is_retry)


def run_compliance_workflow(raw_id: int, run_id: int, is_retry: bool) -> None:
    started_step = tools["create_adk_run_step"](
        run_id=run_id,
        step="google_adk",
        status="started",
        data={"raw_id": raw_id, "is_retry": is_retry},
    )
    started_step_id = started_step.get("id")
    # Finish the "started" step immediately after creation
    if started_step_id:
        tools["finish_adk_run_step"](started_step_id)

    # Try Google ADK first
    use_fallback = False
    result = None
    error_message = None

    try:
        result = asyncio.run(
            run_google_adk_compliance(
                raw_id=raw_id,
                session_id=f"run-{run_id}",
                run_id=run_id,
            )
        )
    except Exception as e:
        error_message = str(e)
        # Check if it's a rate limit error - fall back to manual workflow
        if _is_rate_limit_error(e):
            use_fallback = True
            # Mark Google ADK step as skipped due to rate limit
            skipped_step = tools["create_adk_run_step"](
                run_id=run_id,
                step="google_adk",
                status="failed",
                error=error_message,
                error_code="GOOGLE_ADK_RATE_LIMIT",
                data={"fallback_to_manual": True},
            )
            skipped_step_id = skipped_step.get("id")
            if skipped_step_id:
                tools["finish_adk_run_step"](skipped_step_id)
        else:
            # Other errors - fail completely
            failed_step = tools["create_adk_run_step"](
                run_id=run_id,
                step="google_adk",
                status="failed",
                error=error_message,
                error_code="GOOGLE_ADK_EXCEPTION",
            )
            failed_step_id = failed_step.get("id")
            if failed_step_id:
                tools["finish_adk_run_step"](failed_step_id)
            tools["update_adk_run"](
                run_id=run_id,
                status="failed",
                error=error_message,
                error_code="GOOGLE_ADK_EXCEPTION",
            )
            return

    # Check if result has an error (but not rate limit - that's handled above)
    if result and isinstance(result, dict):
        error = result.get("error")
        if error and error != "unknown_error":
            # Check if it's a rate limit in the result
            debug_info = result.get("debug_info", {})
            if isinstance(debug_info, dict):
                error_str = str(debug_info.get("db_fallback_error", ""))
                if _is_rate_limit_error(Exception(error_str)):
                    use_fallback = True
                else:
                    # Other errors - fail
                    error_code = (
                        "GOOGLE_ADK_NO_FINAL_OUTPUT"
                        if error == "no_final_output"
                        else "GOOGLE_ADK_FAILED"
                    )
                    failed_step = tools["create_adk_run_step"](
                        run_id=run_id,
                        step="google_adk",
                        status="failed",
                        error=str(error),
                        error_code=error_code,
                        data=(
                            result.get("debug_info")
                            if isinstance(result, dict)
                            else None
                        ),
                    )
                    failed_step_id = failed_step.get("id")
                    if failed_step_id:
                        tools["finish_adk_run_step"](failed_step_id)
                    tools["update_adk_run"](
                        run_id=run_id,
                        status="failed",
                        error=str(error),
                        error_code=error_code,
                    )
                    return

    # If we need to fall back to manual workflow
    if use_fallback:
        try:
            manual_result = _run_manual_workflow(
                raw_id=raw_id, run_id=run_id, is_retry=is_retry
            )
            if manual_result.get("status") == "completed":
                # Manual workflow succeeded
                tools["update_adk_run"](
                    run_id=run_id,
                    status="completed",
                    processed_id=manual_result.get("processed_id"),
                    report_id=manual_result.get("report_id"),
                    error=None,
                    error_code=None,
                )
                return
            else:
                # Manual workflow failed
                tools["update_adk_run"](
                    run_id=run_id,
                    status="failed",
                    error=manual_result.get("error", "Manual workflow failed"),
                    error_code="MANUAL_WORKFLOW_FAILED",
                )
                return
        except Exception as e:
            # Manual workflow exception
            tools["update_adk_run"](
                run_id=run_id,
                status="failed",
                error=f"Manual workflow exception: {str(e)}",
                error_code="MANUAL_WORKFLOW_EXCEPTION",
            )
            return

    # Google ADK succeeded
    if result and isinstance(result, dict) and not result.get("error"):
        success_step = tools["create_adk_run_step"](
            run_id=run_id,
            step="google_adk",
            status="success",
            data={
                "processed_id": result.get("processed_id"),
                "report_id": result.get("report_id"),
                "risk_score": result.get("risk_score"),
                "violation_count": result.get("violation_count"),
            },
        )
        success_step_id = success_step.get("id")
        if success_step_id:
            tools["finish_adk_run_step"](success_step_id)

        tools["update_adk_run"](
            run_id=run_id,
            status="completed",
            processed_id=result.get("processed_id"),
            report_id=result.get("report_id"),
            error=None,
            error_code=None,
        )
    else:
        # Unexpected state
        tools["update_adk_run"](
            run_id=run_id,
            status="failed",
            error="Unexpected result from Google ADK",
            error_code="GOOGLE_ADK_UNEXPECTED",
        )
