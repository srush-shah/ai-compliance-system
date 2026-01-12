import re
from difflib import SequenceMatcher
from typing import Any, Dict, Iterable, List


def _snippet(text: str, start: int, end: int, window: int = 80) -> str:
    left = max(start - window, 0)
    right = min(end + window, len(text))
    return text[left:right].strip()


def _semantic_score(a: str, b: str) -> float:
    return SequenceMatcher(None, a.lower(), b.lower()).ratio()


def evaluate_rules(
    rules: Iterable[Dict[str, Any]],
    sections: Iterable[Dict[str, Any]],
) -> List[Dict[str, Any]]:
    violations: List[Dict[str, Any]] = []

    for rule in rules:
        if not rule.get("is_active", True):
            continue

        pattern_type = rule.get("pattern_type", "keyword")
        needle = (rule.get("pattern") or rule.get("name") or "").strip()
        description = (rule.get("description") or "").strip()
        remediation = rule.get("remediation")

        for section in sections:
            text = str(section.get("text", ""))
            if not text:
                continue

            if pattern_type == "regex":
                try:
                    match = re.search(needle, text, flags=re.IGNORECASE)
                except re.error:
                    match = None

                if match:
                    start, end = match.span()
                    violations.append(
                        {
                            "rule_id": rule.get("id"),
                            "rule": rule.get("name"),
                            "severity": rule.get("severity"),
                            "evidence": _snippet(text, start, end),
                            "location": {
                                "chunk_id": section.get("chunk_id"),
                                "label": section.get("label"),
                            },
                            "confidence": 0.9,
                            "recommended_fix": remediation,
                        }
                    )
            elif pattern_type == "semantic":
                intent = description or needle
                score = _semantic_score(intent, text)
                if score >= 0.75:
                    violations.append(
                        {
                            "rule_id": rule.get("id"),
                            "rule": rule.get("name"),
                            "severity": rule.get("severity"),
                            "evidence": text[:200],
                            "location": {
                                "chunk_id": section.get("chunk_id"),
                                "label": section.get("label"),
                            },
                            "confidence": round(score, 2),
                            "recommended_fix": remediation,
                        }
                    )
            else:
                if needle and needle.lower() in text.lower():
                    start = text.lower().find(needle.lower())
                    end = start + len(needle)
                    violations.append(
                        {
                            "rule_id": rule.get("id"),
                            "rule": rule.get("name"),
                            "severity": rule.get("severity"),
                            "evidence": _snippet(text, start, end),
                            "location": {
                                "chunk_id": section.get("chunk_id"),
                                "label": section.get("label"),
                            },
                            "confidence": 0.7,
                            "recommended_fix": remediation,
                        }
                    )

    return violations
