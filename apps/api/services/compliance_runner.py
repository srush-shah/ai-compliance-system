import asyncio

from adk.tools.tools_registry import get_adk_tools
from google_adk.runner import run_google_adk_compliance

tools = get_adk_tools()


def run_compliance_workflow(raw_id: int, run_id: int, is_retry: bool) -> None:
    started_step = tools["create_adk_run_step"](
        run_id=run_id,
        step="google_adk",
        status="started",
        data={"raw_id": raw_id, "is_retry": is_retry},
    )
    started_step_id = started_step.get("id")

    try:
        result = asyncio.run(
            run_google_adk_compliance(
                raw_id=raw_id,
                session_id=f"run-{run_id}",
                run_id=run_id,
            )
        )
    except Exception as e:
        tools["create_adk_run_step"](
            run_id=run_id,
            step="google_adk",
            status="failed",
            error=str(e),
            error_code="GOOGLE_ADK_EXCEPTION",
        )
        tools["update_adk_run"](
            run_id=run_id,
            status="failed",
            error=str(e),
            error_code="GOOGLE_ADK_EXCEPTION",
        )
        if started_step_id:
            tools["finish_adk_run_step"](started_step_id)
        return

    error = result.get("error") if isinstance(result, dict) else "unknown_error"

    if error:
        error_code = (
            "GOOGLE_ADK_NO_FINAL_OUTPUT"
            if error == "no_final_output"
            else "GOOGLE_ADK_FAILED"
        )

        tools["create_adk_run_step"](
            run_id=run_id,
            step="google_adk",
            status="failed",
            error=str(error),
            error_code=error_code,
            data=result.get("debug_info") if isinstance(result, dict) else None,
        )
        tools["update_adk_run"](
            run_id=run_id,
            status="failed",
            error=str(error),
            error_code=error_code,
        )
        if started_step_id:
            tools["finish_adk_run_step"](started_step_id)
        return

    # success
    tools["create_adk_run_step"](
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

    tools["update_adk_run"](
        run_id=run_id,
        status="completed",
        processed_id=result.get("processed_id"),
        report_id=result.get("report_id"),
        error=None,
        error_code=None,
    )

    if started_step_id:
        tools["finish_adk_run_step"](started_step_id)
