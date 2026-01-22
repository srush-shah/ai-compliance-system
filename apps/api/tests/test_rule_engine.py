from services.rule_engine import evaluate_rules


def test_evaluate_rules_keyword_regex_semantic():
    rules = [
        {
            "id": 1,
            "name": "Detect SSN",
            "pattern_type": "keyword",
            "pattern": "SSN",
            "severity": "high",
            "remediation": "Remove SSNs.",
        },
        {
            "id": 2,
            "name": "Detect Email",
            "pattern_type": "regex",
            "pattern": r"[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}",
            "severity": "medium",
            "remediation": "Mask emails.",
        },
        {
            "id": 3,
            "name": "Detect API key",
            "pattern_type": "semantic",
            "description": "Exposes an API key in plaintext",
            "severity": "medium",
            "remediation": "Rotate credentials.",
        },
    ]

    sections = [
        {
            "chunk_id": "c1",
            "label": "body",
            "text": "Customer SSN 123-45-6789 with email test@example.com.",
        },
        {
            "chunk_id": "c2",
            "label": "footer",
            "text": "Exposes an API key in plaintext for quick setup.",
        },
    ]

    violations = evaluate_rules(rules, sections)

    assert {violation["rule_id"] for violation in violations} == {1, 2, 3}
    keyword_violation = next(v for v in violations if v["rule_id"] == 1)
    regex_violation = next(v for v in violations if v["rule_id"] == 2)
    semantic_violation = next(v for v in violations if v["rule_id"] == 3)

    assert keyword_violation["severity"] == "high"
    assert "SSN" in keyword_violation["evidence"]
    assert regex_violation["severity"] == "medium"
    assert "example.com" in regex_violation["evidence"]
    assert semantic_violation["confidence"] >= 0.75
    assert semantic_violation["location"]["chunk_id"] == "c2"
