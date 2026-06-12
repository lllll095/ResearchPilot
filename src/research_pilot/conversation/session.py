# src/research_pilot/conversation/session.py

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


class ConversationMessage(BaseModel):
    """One message in a persistent conversation session."""

    role: str
    content: str
    created_at: str = Field(default_factory=lambda: datetime.now().isoformat())
    metadata: dict[str, Any] = Field(default_factory=dict)


class ConversationSession(BaseModel):
    """Persistent multi-turn conversation state."""

    session_id: str
    created_at: str = Field(default_factory=lambda: datetime.now().isoformat())
    updated_at: str = Field(default_factory=lambda: datetime.now().isoformat())
    messages: list[ConversationMessage] = Field(default_factory=list)
    summary: str = ""
    metadata: dict[str, Any] = Field(default_factory=dict)

    def add_message(
        self,
        role: str,
        content: str,
        metadata: dict[str, Any] | None = None,
    ) -> None:
        self.messages.append(
            ConversationMessage(
                role=role,
                content=content,
                metadata=metadata or {},
            )
        )
        self.updated_at = datetime.now().isoformat()

    def recent_messages(self, max_messages: int = 8) -> list[ConversationMessage]:
        if max_messages <= 0:
            return []
        return self.messages[-max_messages:]