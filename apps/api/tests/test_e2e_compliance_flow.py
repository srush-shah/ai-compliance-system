from fastapi.testclient import TestClient


def test_upload_runs_compliance_and_returns_report(
    client: TestClient, monkeypatch
) -> None:
    from adk.tools import tools_registry
    from routers import upload as upload_router

    def fake_run_compliance_workflow(raw_id: int, run_id: int, is_retry: bool) -> None:
        tools = tools_registry.get_adk_tools()
        processed = tools["create_processed_data"](
            raw_id=raw_id, structured={"sections": [{"text": "sample"}]}
        )
        report_content = {
            "processed_id": processed["id"],
            "violations": [
                {
                    "rule": "Test Rule",
                    "severity": "high",
                    "details": {"rule_id": "T-1"},
                }
            ],
            "risk_score": 42,
        }
        report = tools["create_report"](
            processed_id=processed["id"],
            score=42,
            summary="Test report",
            content=report_content,
        )
        tools["update_adk_run"](
            run_id=run_id,
            status="completed",
            processed_id=processed["id"],
            report_id=report["id"],
            error=None,
            error_code=None,
        )

    monkeypatch.setattr(upload_router, "run_compliance_workflow", fake_run_compliance_workflow)

    headers = {"Authorization": "Bearer test-token"}
    files = {"file": ("sample.txt", b"sample payload")}
    response = client.post("/upload", headers=headers, files=files)

    assert response.status_code == 200
    payload = response.json()
    assert payload["workflow_started"] is True

    run_id = payload["run_id"]
    run_response = client.get(f"/compliance/runs/{run_id}", headers=headers)

    assert run_response.status_code == 200
    run_payload = run_response.json()
    assert run_payload["status"] == "completed"
    assert run_payload["report_id"] is not None

    report_id = run_payload["report_id"]
    report_response = client.get(f"/reports/{report_id}.json", headers=headers)

    assert report_response.status_code == 200
    report_payload = report_response.json()
    assert report_payload["risk_score"] == 42
    assert report_payload["violations"][0]["rule"] == "Test Rule"
