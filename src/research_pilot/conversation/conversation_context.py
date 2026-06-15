# src/research_pilot/conversation/conversation_context.py

from typing import Any

from research_pilot.conversation.session import ConversationSession


class ConversationContextBuilder:
    """Build a conversation-aware user request for the existing ask workflow."""

    def __init__(
        self,
        max_messages: int = 8,
        max_turn_memories: int = 4,
    ):
        self.max_messages = max_messages
        self.max_turn_memories = max_turn_memories

    def build_user_input(
        self,
        session: ConversationSession,
        current_user_input: str,
    ) -> str:
        recent_messages = session.recent_messages(self.max_messages)
        recent_turn_memory = self._recent_turn_memory(session)

        if not recent_messages and not session.summary and not recent_turn_memory:
            return current_user_input

        sections: list[str] = []

        if session.summary.strip():
            sections.append(
                "Persistent session summary:\n"
                f"{session.summary.strip()}"
            )

        if recent_turn_memory:
            sections.append(
                "Recent structured turn memory:\n"
                + recent_turn_memory
            )

        if recent_messages:
            history_lines = []

            for message in recent_messages:
                role = message.role
                content = message.content.strip()

                if not content:
                    continue

                history_lines.append(f"{role}: {content}")

            if history_lines:
                sections.append(
                    "Recent conversation history:\n"
                    + "\n\n".join(history_lines)
                )

        sections.append(
            "Current user request:\n"
            f"{current_user_input.strip()}"
        )

        sections.append(
            "Instruction:\n"
            "Use the persistent summary, structured turn memory, and recent conversation "
            "history only to resolve references such as 'it', 'that', 'the previous tool', "
            "'刚才那个', or '继续'. Answer the current user request directly. "
            "Do not summarize the conversation unless the user asks for a summary."
        )

        return "\n\n---\n\n".join(sections)

    def _recent_turn_memory(self, session: ConversationSession) -> str:
        memories: list[dict[str, Any]] = []

        for message in reversed(session.messages):
            if message.role != "assistant":
                continue

            memory = message.metadata.get("turn_memory")
            if isinstance(memory, dict):
                memories.append(memory)

            if len(memories) >= self.max_turn_memories:
                break

        memories.reverse()

        if not memories:
            return ""

        blocks: list[str] = []

        for idx, memory in enumerate(memories, start=1):
            lines = [f"Turn memory {idx}:"]

            user_input = memory.get("user_input")
            if user_input:
                lines.append(f"- User input: {user_input}")

            code_files = memory.get("code_files") or []
            if code_files:
                lines.append("- Code files involved:")
                for file in code_files[:8]:
                    lines.append(f"  - {file}")

            code_search_queries = memory.get("code_search_queries") or []
            if code_search_queries:
                lines.append("- Code search queries:")
                for query in code_search_queries[:5]:
                    lines.append(f"  - {query}")

            evidence_sources = memory.get("evidence_sources") or []
            if evidence_sources:
                lines.append("- Evidence sources:")
                for source in evidence_sources[:8]:
                    lines.append(f"  - {source}")

            report_paths = memory.get("report_paths") or []
            if report_paths:
                lines.append("- Report paths:")
                for path in report_paths[:5]:
                    lines.append(f"  - {path}")

            blocks.append("\n".join(lines))

        return "\n\n".join(blocks)