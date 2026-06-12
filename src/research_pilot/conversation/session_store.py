# src/research_pilot/conversation/session_store.py

import re
from pathlib import Path

from research_pilot.config import settings
from research_pilot.conversation.session import ConversationSession


class ConversationSessionStore:
    """Save and load conversation sessions from workspace/sessions."""

    def __init__(self, base_dir: Path | None = None):
        self.base_dir = base_dir or (Path(settings.workspace) / "sessions")
        self.base_dir.mkdir(parents=True, exist_ok=True)

    def load_or_create(self, session_id: str) -> ConversationSession:
        safe_id = self._safe_session_id(session_id)
        path = self._session_path(safe_id)

        if not path.exists():
            return ConversationSession(session_id=safe_id)

        text = path.read_text(encoding="utf-8")
        return ConversationSession.model_validate_json(text)

    def save(self, session: ConversationSession) -> Path:
        safe_id = self._safe_session_id(session.session_id)
        session.session_id = safe_id

        path = self._session_path(safe_id)
        path.write_text(
            session.model_dump_json(indent=2),
            encoding="utf-8",
        )
        return path

    def list_sessions(self) -> list[str]:
        return sorted(path.stem for path in self.base_dir.glob("*.json"))

    def _session_path(self, session_id: str) -> Path:
        return self.base_dir / f"{session_id}.json"

    @staticmethod
    def _safe_session_id(session_id: str) -> str:
        session_id = session_id.strip() or "default"
        return re.sub(r"[^a-zA-Z0-9_.-]+", "_", session_id)