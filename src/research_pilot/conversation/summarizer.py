# src/research_pilot/conversation/summarizer.py

from research_pilot.conversation.session import ConversationMessage, ConversationSession
from research_pilot.core.llm_client import OpenAICompatibleLLMClient


class ConversationSummarizer:
    """Compress older conversation messages into a persistent session summary.

    The raw messages are kept in the session file for auditability.
    The summary is used to keep future prompts shorter.
    """

    def __init__(self, llm_client: OpenAICompatibleLLMClient):
        self.llm_client = llm_client

    def maybe_summarize(
        self,
        session: ConversationSession,
        keep_recent: int = 8,
        min_new_messages: int = 4,
    ) -> bool:
        """Summarize older messages if enough unsummarized messages exist.

        Returns True if the session summary was updated.
        """

        if keep_recent < 1:
            keep_recent = 1

        total_messages = len(session.messages)

        # Keep the most recent messages in raw form.
        cutoff = max(0, total_messages - keep_recent)

        summarized_count = int(session.metadata.get("summarized_message_count", 0))

        # Nothing new to summarize.
        if cutoff <= summarized_count:
            return False

        # Avoid summarizing too frequently.
        if cutoff - summarized_count < min_new_messages:
            return False

        messages_to_summarize = session.messages[summarized_count:cutoff]

        if not messages_to_summarize:
            return False

        updated_summary = self._summarize_messages(
            previous_summary=session.summary,
            messages=messages_to_summarize,
        )

        session.summary = updated_summary.strip()
        session.metadata["summarized_message_count"] = cutoff

        return True

    def _summarize_messages(
        self,
        previous_summary: str,
        messages: list[ConversationMessage],
    ) -> str:
        messages_text = self._render_messages(messages)

        system_prompt = """You are a conversation memory compressor.

Your job is to update a persistent session summary for an agent system.

Rules:
- Preserve user goals, decisions, preferences, constraints, and important technical facts.
- Preserve file paths, commands, function/class names, and project-specific terminology.
- Preserve unresolved issues and known limitations.
- Do not include irrelevant chit-chat.
- Do not invent details.
- Write a concise but useful summary.
- Output only the updated summary text.
"""

        user_prompt = f"""Previous session summary:
{previous_summary or "(empty)"}

New conversation messages to compress:
{messages_text}

Update the session summary.
"""

        response = self.llm_client.complete(
            [
                {
                    "role": "system",
                    "content": system_prompt,
                },
                {
                    "role": "user",
                    "content": user_prompt,
                },
            ]
        )

        return response.strip()

    @staticmethod
    def _render_messages(messages: list[ConversationMessage]) -> str:
        lines: list[str] = []

        for message in messages:
            role = message.role
            content = message.content.strip()

            if not content:
                continue

            lines.append(f"{role}: {content}")

        return "\n\n".join(lines)