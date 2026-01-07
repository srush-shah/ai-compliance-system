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


async def run_google_adk_compliance(raw_id: int, session_id: str) -> Dict[str, Any]:
    """
    Run Google ADK compliance workflow.
    Extracts the final model text and parses JSON, with fallback to database lookup.
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

    prompt = f"Run compliance pipeline for raw_id={raw_id}. Return the final JSON only."

    final_text = None
    all_texts = []  # Collect all text chunks for debugging

    # Run the workflow and collect events
    for event in _runner.run(
        user_id=user_id,
        session_id=session_id,
        new_message=Content(parts=[Part(text=prompt)]),
    ):
        # Try multiple ways to extract text from events
        text_candidates = []

        # Check event.content.parts (most common location)
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

        # Check other possible attributes using getattr
        for attr_name in ["message", "text", "response"]:
            attr_value = getattr(event, attr_name, None)
            if attr_value:
                try:
                    # If it's a string, use it directly
                    if isinstance(attr_value, str):
                        text_candidates.append(attr_value)
                    # If it has a text attribute
                    elif hasattr(attr_value, "text"):
                        t = getattr(attr_value, "text", None)
                        if t:
                            text_candidates.append(t)
                    # If it has content.parts
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

        # Update final_text with the latest text found
        for text in text_candidates:
            if text:
                final_text = text
                all_texts.append(text)

    # Try to parse JSON from the final text
    if final_text:
        text_to_parse = final_text.strip()

        # Try to extract JSON from markdown code blocks
        json_match = re.search(
            r"```(?:json)?\s*(\{.*?\})\s*```", text_to_parse, re.DOTALL
        )
        if json_match:
            text_to_parse = json_match.group(1)

        # If no code block, try to find JSON object in the text
        if not json_match:
            json_match = re.search(r"\{.*\}", text_to_parse, re.DOTALL)
            if json_match:
                text_to_parse = json_match.group(0)

        # Parse JSON
        try:
            result = json.loads(text_to_parse)
            # Validate that we have the expected keys
            if isinstance(result, dict) and "processed_id" in result:
                return result
        except json.JSONDecodeError:
            pass  # Fall through to database lookup

    # Fallback: Extract result from database using timestamp-based lookup
    # Query for records created during this run (after run_start_time)
    try:
        from adk.tools.db_tools import get_violations_by_processed_id
        from db import SessionLocal
        from models import ProcessedData, Report
        from sqlalchemy.orm import Session

        db: Session = SessionLocal()
        try:
            # Get the most recent processed_data created after run start
            # (or if none found, get the most recent one as fallback)
            processed = (
                db.query(ProcessedData)
                .filter(ProcessedData.created_at >= run_start_time)
                .order_by(ProcessedData.id.desc())
                .first()
            )

            # If no record found after run start, get the most recent one
            if not processed:
                processed = (
                    db.query(ProcessedData).order_by(ProcessedData.id.desc()).first()
                )

            if processed:
                # Extract processed_id from the model instance
                # Type checker may complain, but at runtime processed.id is an int
                processed_id = getattr(processed, "id", None)

                if processed_id is not None:
                    # Get violations for this processed_id using the existing function
                    violations = get_violations_by_processed_id(processed_id)  # type: ignore
                    violation_count = (
                        len(violations) if isinstance(violations, list) else 0
                    )

                    # Get the most recent report created after run start
                    report = (
                        db.query(Report)
                        .filter(Report.created_at >= run_start_time)
                        .order_by(Report.id.desc())
                        .first()
                    )

                    # If no report found after run start, get the most recent one
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
                    }
        finally:
            db.close()
    except Exception as e:
        # If database lookup also fails, return error
        return {
            "error": "no_final_output",
            "debug_info": {
                "text_chunks_collected": len(all_texts),
                "db_fallback_error": str(e),
            },
        }

    # If we get here, we couldn't extract the result
    return {
        "error": "no_final_output",
        "debug_info": {
            "text_chunks_collected": len(all_texts),
        },
    }
