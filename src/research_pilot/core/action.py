from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


class ActionType(str, Enum):
    """Possible action types produced by an Agent."""

    TOOL_CALL = "tool_call"
    FINAL_ANSWER = "final_answer"


class AgentAction(BaseModel):
    """An action produced by the Agent.

    The action can either be:
    - a tool call
    - a final answer
    """

    action_type: ActionType
    tool_name: str | None = None
    tool_input: dict[str, Any] = Field(default_factory=dict)
    final_answer: str | None = None
    thought_summary: str | None = None
