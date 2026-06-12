# src/research_pilot/conversation/conversation_context.py

from research_pilot.conversation.session import ConversationSession


class ConversationContextBuilder:
    """Build a conversation-aware user request for the existing ask workflow."""

    def __init__(self, max_messages: int = 8):
        self.max_messages = max_messages

    def build_user_input(
        self,
        session: ConversationSession,
        current_user_input: str,
    ) -> str:
        recent_messages = session.recent_messages(self.max_messages)

        if not recent_messages and not session.summary:
            return current_user_input

        sections: list[str] = []

        if session.summary.strip():
            sections.append(
                "Conversation summary:\n"
                f"{session.summary.strip()}"
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
                    + "\n".join(history_lines)
                )

        sections.append(
            "Current user request:\n"
            f"{current_user_input.strip()}"
        )

        sections.append(
            "Instruction:\n"
            "Use the conversation history only to resolve references such as "
            "'it', 'that', 'the previous tool', or '刚才那个'. "
            "Answer the current user request directly."
        )

        return "\n\n".join(sections)