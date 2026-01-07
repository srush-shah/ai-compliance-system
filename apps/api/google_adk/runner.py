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

    # Run the workflow and collect events
    for event in _runner.run(
        user_id=user_id,
        session_id=session_id,
        new_message=Content(parts=[Part(text=prompt)]),
    ):
        text_candidates: list[str] = []

        # event.content.parts
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

            # 2) Last resort: timestamp heuristic (existing logic)
            processed = (
                db.query(ProcessedData)
                .filter(ProcessedData.created_at >= run_start_time)
                .order_by(ProcessedData.id.desc())
                .first()
            )

            if not processed:
                processed = (
                    db.query(ProcessedData).order_by(ProcessedData.id.desc()).first()
                )

            if processed:
                processed_id = getattr(processed, "id", None)

                if processed_id is not None:
                    violations = get_violations_by_processed_id(processed_id)  # type: ignore
                    violation_count = (
                        len(violations) if isinstance(violations, list) else 0
                    )

                    report = (
                        db.query(Report)
                        .filter(Report.created_at >= run_start_time)
                        .order_by(Report.id.desc())
                        .first()
                    )
                    if not report:
                        report = db.query(Report).order_by(Report.id.desc()).first()

                    report_id = getattr(report, "id", None) if report else None
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
                "text_chunks_collected": len(all_texts),
                "db_fallback_error": str(e),
            },
        }

    return {
        "error": "no_final_output",
        "debug_info": {"text_chunks_collected": len(all_texts)},
    }
