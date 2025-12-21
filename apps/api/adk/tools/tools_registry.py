"""
ADK Tool Registry

This file exposes database tools to ADK agents
without executing them automatically.
"""

from typing import Callable, Dict

# Import existing db tools (already tested)
from adk.tools.db_tools import (
    create_processed_data,
    create_report,
    create_violation,
    get_policy_rules,
    get_processed_data_by_id,
    get_raw_data_by_id,
    get_report_by_id,
    get_violations_by_processed_id,
    log_agent_action,
)


def get_adk_tools() -> Dict[str, Callable]:
    """
    Single source of truth for tools ADK agents can use.
    """

    return {
        "get_raw_data_by_id": get_raw_data_by_id,
        "get_processed_data_by_id": get_processed_data_by_id,
        "get_policy_rules": get_policy_rules,
        "get_report_by_id": get_report_by_id,
        "get_violations_by_processed_id": get_violations_by_processed_id,
        "create_processed_data": create_processed_data,
        "create_violation": create_violation,
        "create_report": create_report,
        "log_agent_action": log_agent_action,
    }
