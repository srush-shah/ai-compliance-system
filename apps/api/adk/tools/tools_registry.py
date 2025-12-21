"""
ADK Tool Registry

This file exposes database tools to ADK agents
without executing them automatically.
"""

from typing import Callable, Dict

# Import existing db tools (already tested)
from adk.tools.db_tools import (
    create_violation,
    fetch_policy_rules,
    fetch_processed_data,
    log_agent_action,
)


def get_adk_tools() -> Dict[str, Callable]:
    """
    Single source of truth for tools ADK agents can use.
    """

    return {
        "fetch_processed_data": fetch_processed_data,
        "fetch_policy_rules": fetch_policy_rules,
        "create_violation": create_violation,
        "log_agent_action": log_agent_action,
    }
