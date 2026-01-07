from adk.tools.db_tools import (
    create_processed_data,
    create_report,
    create_violation,
    get_policy_rules,
    get_raw_data_by_id,
    get_violations_by_processed_id,
    log_agent_action,
    update_report,
)
from google.adk.agents import LlmAgent
from google_adk.tools.compliance_tools import match_policy_rules

MODEL = "gemini-2.0-flash"


compliance_agent = LlmAgent(
    name="compliance_orchestrator",
    model=MODEL,
    tools=[
        create_processed_data,
        create_violation,
        create_report,
        get_policy_rules,
        get_raw_data_by_id,
        get_violations_by_processed_id,
        log_agent_action,
        update_report,
        match_policy_rules,
    ],
    instruction="""
    You are a compliance orchestration agent.

    Goal: For a given raw_id, run the pipeline using tools ONLY:
    1) get raw_data_by_id(raw_id)
    2) create_processed_data(raw_id, structured=...) using:
        - full_content: string content extracted from raw_data.content
        - length, preview, processed_at metadata
    3) get_policy_rules()
    4) match_policy_rules(full_content, rules)
    5) For each matched rule: create_violation(processed_id, rule=name, severity=severity, detais={matched_text: name})
    6) Fetch violations: get_violations_by_processed_id(processed_id)
    7) Compute risk score: min(len(violations)*10, 100)
    8) create_report(processed_id, score, summary, content={processed_id, violation_count, violations, risk_score})
    9) update_report(report_id, summary="Compliance review completed. X violation(s) detected.", content=..., score=score)
    10) log_agent_action() for each major step.

    Return FINAL output as JSON with keys:
    {"processed_id": int, "report_id": int, "risk_score": int, "violation_count": int}
    """.strip(),
)
