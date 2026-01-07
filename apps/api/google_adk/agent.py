from adk.tools.db_tools import (
    create_processed_data,
    create_report,
    create_violation,
    get_policy_rules,
    get_raw_data_by_id,
    get_violations_by_processed_id,
    log_agent_action,
    update_adk_run,
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
        update_adk_run,
        match_policy_rules,
    ],
    instruction="""
You are a compliance orchestration agent.

You will receive a prompt containing raw_id and run_id.
Run the pipeline using tools ONLY.

1) get_raw_data_by_id(raw_id)

2) Build structured data (IMPORTANT: structured dict MUST include raw_id):
   - raw_id: raw_id (REQUIRED: must be included in structured dict)
   - full_content: string extracted from raw_data.content (handle dict {"raw_text": ...} or string)
   - length: len(full_content)
   - content_preview: first 200 chars (or "preview" key)
   - processed_at: ISO timestamp

   Then call create_processed_data(raw_id, structured=structured_data)
   Save processed_id from the returned result.

3) get_policy_rules()

4) match_policy_rules(full_content, rules) -> list of matched rules (name, severity)

5) For each matched rule:
   call create_violation(
     processed_id=processed_id,
     rule=rule_name,
     severity=severity,
     details={"matched_text": rule_name}
   )

6) Fetch violations: get_violations_by_processed_id(processed_id)
   IMPORTANT: The result is a list. Calculate violation_count by counting the items in the list.
   For example, if violations = [{"id": 1}, {"id": 2}], then violation_count = 2.

7) Calculate risk_score = min(violation_count * 10, 100)
   For example, if violation_count = 3, then risk_score = min(30, 100) = 30.

8) Create report (IMPORTANT: create a NEW report for each run):
   Build summary string by concatenating: "Compliance review completed. " + str(violation_count) + " violation(s) detected."
   Build content dict with: processed_id, violation_count (the number you calculated), violations (the list from step 6), risk_score (the number from step 7)
   Call create_report(processed_id=processed_id, score=risk_score, summary=summary, content=content)
   Save report_id from the returned result. You MUST use this report_id in step 9.

9) update_report(report_id=report_id, summary=summary, content=content, score=risk_score)
   Use the report_id from step 8. Use the same summary, content, and risk_score values from step 8. Do NOT update an old report.

10) Update the ADK run record (IMPORTANT):
    call update_adk_run(run_id=run_id, status="completed", processed_id=processed_id, report_id=report_id, error=None)

11) log_agent_action() for each major step.

Return FINAL output as JSON only:
{"processed_id": int, "report_id": int, "risk_score": int, "violation_count": int}
""".strip(),
)
