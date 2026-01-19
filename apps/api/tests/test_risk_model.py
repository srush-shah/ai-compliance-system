from datetime import datetime, timezone

import pytest

from services.risk_model import score_risk


def test_score_risk_accounts_for_recency_and_repeats():
    now = datetime.now(timezone.utc).isoformat()
    violations = [
        {
            "severity": "high",
            "details": {"rule_id": "R1", "confidence": 0.9},
            "created_at": now,
        },
        {
            "severity": "high",
            "details": {"rule_id": "R1", "confidence": 0.9},
            "created_at": now,
        },
    ]

    result = score_risk(violations)

    assert result["tier"] == "Medium"
    assert result["score"] == pytest.approx(41.58, rel=1e-3)
    assert len(result["breakdown"]) == 2
    assert result["breakdown"][1]["repeat_multiplier"] == pytest.approx(1.1, rel=1e-3)
