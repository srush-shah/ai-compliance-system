"""
ADK Data Engineer Agent

Fetches raw data, processed it into structured format, stores processed data, and logs agent actions using ADK tools.
"""

from datetime import datetime, timezone
from typing import Dict

from adk.tools.tools_registry import get_adk_tools


class DataEngineerADKAgent:
    def __init__(self):
        self.name = "Data Engineer"
        self.tools = get_adk_tools()

    def describe(self):
        """Debug helper to verify available tools."""
        return {"agent": self.name, "available_tools": list(self.tools.keys())}

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

        # 2. Basic structuring/cleaning
        # For now, we just wrap the data in a dict and add metadata
        structured_data = {
            "length": len(raw["content"]),
            "content_preview": raw["content"][:200],
            "full_content": raw["content"],
            "processed_at": datetime.now(timezone.utc).isoformat(),
        }

        # 3. Store as processed data in DB
        db = self.tools.get("create_processed_data")

        processed_id = db(raw_id=raw_id, structured=structured_data)["id"]

        # 4. Log Agent Action
        self.tools["log_agent_action"](
            agent_name=self.name,
            action="processed_raw_data",
            details={"raw_id": raw_id, "processed_id": processed_id},
        )

        return {"processed_id": processed_id, "structured": structured_data}
