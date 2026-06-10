from research_pilot.core.state import AgentState
from research_pilot.core.tool_runtime import ToolRuntime


class ContextManager:
    """Build compact context for the Agent.

    Phase 1 only provides a simple text context.
    Later phases will add context compression and memory retrieval.
    """

    def build_context(self, state: AgentState, tool_runtime: ToolRuntime) -> str:
        recent_steps = state.steps[-5:]

        step_text = "\n".join(
            f"Step {step.step_id}: {step.action.action_type} "
            f"{step.action.tool_name or ''} -> "
            f"{step.observation.content if step.observation else 'no observation'}"
            for step in recent_steps
        )

        tools = ", ".join(tool_runtime.list_tools())

        return f"""User goal:
{state.user_goal}

Available tools:
{tools}

Recent steps:
{step_text}
"""
