"""
ADK Data Engineer Agent

Fetches raw data, processed it into structured format, stores processed data, and logs agent actions using ADK tools.
"""

import json
from datetime import datetime, timezone
from hashlib import sha256
from typing import Dict, Iterable, List, Tuple

from adk.tools.tools_registry import get_adk_tools


class DataEngineerADKAgent:
    def __init__(self):
        self.name = "Data Engineer"
        self.tools = get_adk_tools()

    def _build_sections(self, rows: Iterable[Tuple[str, str]], raw_id: int) -> List[Dict]:
        sections = []
        for index, (label, text) in enumerate(rows):
            chunk_base = f"{raw_id}:{index}:{label}:{text}"
            chunk_id = sha256(chunk_base.encode()).hexdigest()[:16]
            sections.append(
                {
                    "chunk_id": chunk_id,
                    "index": index,
                    "label": label,
                    "text": text,
                }
            )
        return sections

    def _normalize_from_raw(self, content: Dict, raw_id: int) -> Dict:
        file_type = content.get("file_type", "text")
        raw_text = content.get("raw_text", "")
        metadata = {
            "source": content.get("source", "upload"),
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "file_type": file_type,
            "file_name": content.get("file_name"),
        }

        rows: List[Tuple[str, str]] = []

        if file_type == "json" and "parsed_json" in content:
            parsed_json = content.get("parsed_json")
            if isinstance(parsed_json, dict):
                for key, value in parsed_json.items():
                    rows.append((f"json.{key}", f"{value}"))
            elif isinstance(parsed_json, list):
                for index, entry in enumerate(parsed_json):
                    rows.append((f"json[{index}]", f"{entry}"))
        elif file_type == "csv" and "csv_rows" in content:
            csv_rows = content.get("csv_rows", [])
            if isinstance(csv_rows, list):
                for index, row in enumerate(csv_rows):
                    rows.append((f"csv.row.{index}", json.dumps(row)))

        if not rows:
            for index, line in enumerate(str(raw_text).splitlines()):
                if not line.strip():
                    continue
                rows.append((f"text.line.{index}", line.strip()))

        sections = self._build_sections(rows, raw_id)

        return {
            "metadata": metadata,
            "entities": {"people": [], "orgs": [], "locations": []},
            "sections": sections,
            "normalized_fields": {
                "raw_id": raw_id,
                "section_count": len(sections),
                "char_count": len(str(raw_text)),
            },
            "raw_payload": content,
        }

    def process_raw_data(self, raw_id: int) -> Dict:
        """
        Full processing pipeline:
        1. Fetch raw data
        2. Structure/clean it
        3. Store as processed data
        4. Log the agent action
        """

        # 1. Fetch raw data
        raw = self.tools["get_raw_data_by_id"](raw_id)

        if "error" in raw:
            return {"error": "raw_data not found", "raw_id": raw_id}

        # 2. Deterministic structuring/normalization
        content = raw["content"]
        if not isinstance(content, dict):
            content = {"raw_text": str(content), "file_type": "text", "source": "upload"}

        structured_data = self._normalize_from_raw(content, raw_id)
        structured_data["processed_at"] = datetime.now(timezone.utc).isoformat()

        # 3. Store as processed data in DB
        db = self.tools.get("create_processed_data")
        if db is None:
            return {"error": "'create_processed_data' tool not available", "raw_id": raw_id}

        processed_result = db(raw_id=raw_id, structured=structured_data)
        if not processed_result or "id" not in processed_result:
            return {"error": "failed to store processed data", "raw_id": raw_id}

        processed_id = processed_result["id"]

        # 4. Log Agent Action
        self.tools["log_agent_action"](
            agent_name=self.name,
            action="processed_raw_data",
            details={"raw_id": raw_id, "processed_id": processed_id},
        )

        return {"processed_id": processed_id, "structured": structured_data}

    def run(self, raw_id: int) -> Dict:
        return self.process_raw_data(raw_id=raw_id)
