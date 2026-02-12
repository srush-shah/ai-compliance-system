import json
import re
from datetime import datetime, timezone
from typing import Any, Dict

from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.genai.types import Content, Part
from google_adk.agent import compliance_agent

_session_service = InMemorySessionService()
_runner = Runner(
    agent=compliance_agent,
    app_name="ai_compliance_system",
    session_service=_session_service,
)


async def run_google_adk_compliance(
    raw_id: int, session_id: str, run_id: int
) -> Dict[str, Any]:
    """
    Run Google ADK compliance workflow.
    Extracts the final model text and parses JSON, with fallback to DB lookup.

    Fallback order:
    1) ADKRun by run_id (most reliable)
    2) timestamp heuristic (last resort)
    """

    user_id = "local_user"

    # Record start time BEFORE the run to track database records created during this run
    run_start_time = datetime.now(timezone.utc)

    # Create a new session per run
    await _session_service.create_session(
        app_name="ai_compliance_system",
        user_id=user_id,
        session_id=session_id,
    )

    prompt = f"Run compliance pipeline for raw_id={raw_id} (run_id={run_id}). Return the final JSON only."

    final_text = None
    all_texts: list[str] = []

    # Run the workflow and collect events using async iteration
    try:
        async for event in _runner.run_async(
        user_id=user_id,
        session_id=session_id,
        new_message=Content(parts=[Part(text=prompt)]),
    ):
            text_candidates: list[str] = []

            # Check if this is a final response event
            is_final = getattr(event, "is_final_response", None)
            if callable(is_final):
                try:
                    if is_final():
                        # This is the final response, prioritize its content
                        event_content = getattr(event, "content", None)
                        if event_content:
                            try:
                                parts = getattr(event_content, "parts", []) or []
                                for p in parts:
                                    t = getattr(p, "text", None)
                                    if t:
                                        text_candidates.append(t)
                            except Exception:
                                pass
                except Exception:
                    pass

            # event.content.parts (for all events, including incremental)
        event_content = getattr(event, "content", None)
        if event_content:
            try:
                parts = getattr(event_content, "parts", []) or []
                for p in parts:
                    t = getattr(p, "text", None)
                    if t:
                        text_candidates.append(t)
            except Exception:
                pass

        # other possible attrs
        for attr_name in ["message", "text", "response"]:
            attr_value = getattr(event, attr_name, None)
            if attr_value:
                try:
                    if isinstance(attr_value, str):
                        text_candidates.append(attr_value)
                    elif hasattr(attr_value, "text"):
                        t = getattr(attr_value, "text", None)
                        if t:
                            text_candidates.append(t)
                    elif hasattr(attr_value, "content"):
                        content = getattr(attr_value, "content", None)
                        if content:
                            parts = getattr(content, "parts", []) or []
                            for p in parts:
                                t = getattr(p, "text", None)
                                if t:
                                    text_candidates.append(t)
                except Exception:
                    pass

        for text in text_candidates:
            if text:
                final_text = text
                all_texts.append(text)
    except Exception:
        # Re-raise exceptions (including rate limit errors) to be handled by caller
        raise

    # Try JSON parse from final model text
    if final_text:
        text_to_parse = final_text.strip()

        json_match = re.search(
            r"```(?:json)?\s*(\{.*?\})\s*```", text_to_parse, re.DOTALL
        )
        if json_match:
            text_to_parse = json_match.group(1)
        else:
            json_match = re.search(r"\{.*\}", text_to_parse, re.DOTALL)
            if json_match:
                text_to_parse = json_match.group(0)

        try:
            result = json.loads(text_to_parse)
            if isinstance(result, dict) and "processed_id" in result:
                return result
        except json.JSONDecodeError:
            pass

    # Fallback: DB
    try:
        from adk.tools.db_tools import get_violations_by_processed_id
        from db import SessionLocal
        from models import ADKRun, ProcessedData, Report
        from sqlalchemy import text as sql_text
        from sqlalchemy.orm import Session

        db: Session = SessionLocal()
        try:
            # 1) Most reliable: read ADKRun by run_id
            run = db.query(ADKRun).filter(ADKRun.id == run_id).first()
            if run:
                # If your workflow/agents already wrote these onto ADKRun, trust them.
                if run.processed_id is not None or run.report_id is not None:
                    processed_id = run.processed_id
                    report_id = run.report_id

                    violations = (
                        get_violations_by_processed_id(processed_id)  # type: ignore[arg-type]
                        if processed_id is not None
                        else []
                    )
                    violation_count = (
                        len(violations) if isinstance(violations, list) else 0
                    )
                    risk_score = (
                        min(violation_count * 10, 100) if violation_count > 0 else 0
                    )

                    return {
                        "processed_id": processed_id,
                        "report_id": report_id,
                        "risk_score": risk_score,
                        "violation_count": violation_count,
                        "source": "adk_run",
                    }

            # 2) Query ProcessedData created during this run AND matching raw_id
            # Since ProcessedData has no raw_id column, filter by structured->>'raw_id' = raw_id
            # Use parameterized query for safety (raw_id is int, but still use params)
            processed = (
                db.query(ProcessedData)
                .filter(
                    ProcessedData.created_at >= run_start_time,
                    sql_text(
                        "processed_data.structured->>'raw_id' = :raw_id_val"
                    ).params(raw_id_val=str(raw_id)),
                )
                .order_by(ProcessedData.id.desc())
                .first()
            )

            if processed:
                processed_id = getattr(processed, "id", None)

                if processed_id is not None:
                    violations = get_violations_by_processed_id(processed_id)  # type: ignore
                    violation_count = (
                        len(violations) if isinstance(violations, list) else 0
                    )

                    # Find report for this processed_id created during this run
                    candidate_reports = (
                        db.query(Report)
                        .filter(Report.created_at >= run_start_time)
                        .order_by(Report.id.desc())
                        .all()
                    )
                    report_id = None
                    for r in candidate_reports:
                        content = r.content or {}
                        if (
                            isinstance(content, dict)
                            and content.get("processed_id") == processed_id
                        ):
                            report_id = r.id
                            break
                    risk_score = (
                        min(violation_count * 10, 100) if violation_count > 0 else 0
                    )

                    return {
                        "processed_id": processed_id,
                        "report_id": report_id,
                        "risk_score": risk_score,
                        "violation_count": violation_count,
                        "source": "raw_id_match",
                    }

            # 3) Last resort: timestamp heuristic (only if no raw_id match found)
            processed = (
                db.query(ProcessedData)
                .filter(ProcessedData.created_at >= run_start_time)
                .order_by(ProcessedData.id.desc())
                .first()
            )

            if not processed:
                return {
                    "error": "no_db_artifacts_created",
                    "debug_info": {
                        "raw_id": raw_id,
                        "run_id": run_id,
                        "reason": "no processed_data created after run_start_time matching raw_id",
                        "text_chunks_collected": len(all_texts),
                    },
                }

            if processed:
                processed_id = getattr(processed, "id", None)

                if processed_id is not None:
                    # Verify this processed_data actually matches raw_id (safety check)
                    structured = getattr(processed, "structured", None)
                    if isinstance(structured, dict):
                        structured_raw_id = structured.get("raw_id")
                        if structured_raw_id is not None and str(
                            structured_raw_id
                        ) != str(raw_id):
                            # This belongs to a different raw_id, don't use it
                            return {
                                "error": "no_db_artifacts_created",
                                "debug_info": {
                                    "raw_id": raw_id,
                                    "run_id": run_id,
                                    "reason": f"processed_data {processed_id} belongs to different raw_id {structured_raw_id}",
                                    "text_chunks_collected": len(all_texts),
                                },
                            }

                    violations = get_violations_by_processed_id(processed_id)  # type: ignore
                    violation_count = (
                        len(violations) if isinstance(violations, list) else 0
                    )

                    candidate_reports = (
                        db.query(Report)
                        .filter(Report.created_at >= run_start_time)
                        .order_by(Report.id.desc())
                        .all()
                    )
                    report_id = None
                    for r in candidate_reports:
                        content = r.content or {}
                        if (
                            isinstance(content, dict)
                            and content.get("processed_id") == processed_id
                        ):
                            report_id = r.id
                            break
                    risk_score = (
                        min(violation_count * 10, 100) if violation_count > 0 else 0
                    )

                    return {
                        "processed_id": processed_id,
                        "report_id": report_id,
                        "risk_score": risk_score,
                        "violation_count": violation_count,
                        "source": "timestamp_heuristic",
                    }
        finally:
            db.close()

    except Exception as e:
        return {
            "error": "no_final_output",
            "debug_info": {
                "raw_id": raw_id,
                "run_id": run_id,
                "text_chunks_collected": len(all_texts),
                "db_fallback_error": str(e),
            },
        }

    return {
        "error": "no_final_output",
        "debug_info": {
            "raw_id": raw_id,
            "run_id": run_id,
            "text_chunks_collected": len(all_texts),
        },
    }
