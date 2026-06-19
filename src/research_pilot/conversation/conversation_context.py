# src/research_pilot/conversation/conversation_context.py

from typing import Any

from research_pilot.conversation.session import ConversationSession


class ConversationContextBuilder:
    """Build a conversation-aware user request for the existing ask workflow.

    Key principle: never let old conversation history pollute a new query.
    The persistent session summary is excluded by default because it tends
    to dominate the LLM context and bias the current query toward old topics.
    Only include recent conversation history when the user makes an ambiguous
    reference (e.g. "继续", "它", "it", "that").
    """

    def __init__(
        self,
        max_messages: int = 2,
        max_turn_memories: int = 0,
    ):
        self.max_messages = max_messages
        self.max_turn_memories = max_turn_memories

    def build_user_input(
        self,
        session: ConversationSession,
        current_user_input: str,
    ) -> str:
        recent_messages = session.recent_messages(self.max_messages)
        needs_context = self._needs_conversation_context(current_user_input)

        if not needs_context:
            return current_user_input

        sections: list[str] = []

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
                    "Recent conversation history (for resolving references):\n"
                    + "\n\n".join(history_lines)
                )

        sections.append(
            "Current user request:\n"
            f"{current_user_input.strip()}"
        )

        sections.append(
            "Instruction:\n"
            "Use the recent conversation history only to resolve references "
            "such as 'it', 'that', 'the previous tool', '刚才那个', or '继续'. "
            "The current user request is the primary instruction. "
            "Do NOT carry over topics or queries from previous conversation history "
            "unless the current request explicitly references them. "
            "Ignore the session summary - it is from previous conversations and not relevant."
        )

        return "\n\n---\n\n".join(sections)

    def _needs_conversation_context(self, user_input: str) -> bool:
        """Detect whether the user input makes ambiguous references to previous turns.

        If the input contains a strong technical term (CamelCase like "AgenticRAG"),
        it is probably a NEW topic, not a reference to the previous conversation.
        In that case, do NOT inject history, to avoid polluting the current query.
        """
        import re
        text = user_input.strip()

        if not text:
            return False

        # If the input contains a CamelCase / technical term, it is likely a new topic.
        strong_terms = re.findall(r"\b[A-Z][a-z]+[A-Z][A-Za-z]*\b", text)
        if strong_terms:
            return False

        # Detect ambiguous references
        reference_patterns = [
            "it", "that", "this", "those", "the previous", "the above",
            "continue", "go on", "explain more", "search it", "回答我",
            "它", "这个", "那个", "这些", "那些", "之前", "刚才",
            "继续", "上面的", "还有吗", "说详细点", "搜索一下",
        ]

        text_lower = text.lower()
        for pattern in reference_patterns:
            if pattern in text_lower:
                return True

        return False
