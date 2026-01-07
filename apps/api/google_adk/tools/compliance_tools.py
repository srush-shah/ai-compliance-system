from typing import Dict, List


def match_policy_rules(content_text: str, rules: List[Dict]) -> List[Dict]:
    """
    Deterministic matching tool:
    returns rules whose name appears as substring in content_text (case-insensitive).
    """

    text = (content_text or "").lower()
    matches = []

    for r in rules:
        name = (r.get("name") or "").strip()
        if name and name.lower() in text:
            matches.append(r)

    return matches
