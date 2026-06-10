from typing import Any

from pydantic import BaseModel, Field


class Observation(BaseModel):
    """Result returned by a tool execution."""

    success: bool
    content: str
    metadata: dict[str, Any] = Field(default_factory=dict)
    error: str | None = None
