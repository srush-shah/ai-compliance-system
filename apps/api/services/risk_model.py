from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List

SEVERITY_WEIGHTS = {
    "low": 5,
    "medium": 12,
    "high": 20,
    "critical": 30,
}


def _parse_timestamp(value: str | None) -> datetime | None:
    if not value:
        return None
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None


def score_risk(violations: List[Dict[str, Any]]) -> Dict[str, Any]:
    now = datetime.now(timezone.utc)
    recent_window = now - timedelta(days=7)
    rule_counts: Dict[str, int] = {}

    breakdown: List[Dict[str, Any]] = []
    total = 0.0

    for violation in violations:
        severity = str(violation.get("severity", "medium")).lower()
        base_weight = SEVERITY_WEIGHTS.get(severity, SEVERITY_WEIGHTS["medium"])

        details = violation.get("details") or {}
        confidence = details.get("confidence")
        confidence_factor = float(confidence) if isinstance(confidence, (int, float)) else 0.7

        rule_id = str(details.get("rule_id") or violation.get("rule") or "unknown")
        rule_counts[rule_id] = rule_counts.get(rule_id, 0) + 1

        created_at = violation.get("created_at")
        violation_time = _parse_timestamp(created_at)
        recency_boost = 1.1 if violation_time and violation_time >= recent_window else 1.0

        repeat_multiplier = 1.0 + (rule_counts[rule_id] - 1) * 0.1

        score = base_weight * confidence_factor * recency_boost * repeat_multiplier
        total += score

        breakdown.append(
            {
                "rule": rule_id,
                "severity": severity,
                "base_weight": base_weight,
                "confidence": round(confidence_factor, 2),
                "recency_boost": recency_boost,
                "repeat_multiplier": round(repeat_multiplier, 2),
                "score": round(score, 2),
            }
        )

    capped_score = min(round(total, 2), 100.0)

    if capped_score >= 85:
        tier = "Critical"
    elif capped_score >= 60:
        tier = "High"
    elif capped_score >= 30:
        tier = "Medium"
    else:
        tier = "Low"

    return {
        "score": capped_score,
        "tier": tier,
        "breakdown": breakdown,
    }
