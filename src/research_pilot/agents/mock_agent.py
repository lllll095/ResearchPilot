from research_pilot.core.action import ActionType, AgentAction
from research_pilot.core.state import AgentState


class MockAgentPolicy:
    """A deterministic mock Agent used in Phase 1.

    It simulates how an LLM Agent would decide actions.
    This makes the Agent loop testable before connecting a real model.
    """

    def next_action(self, state: AgentState, context: str) -> AgentAction:
        step_count = len(state.steps)

        if step_count == 0:
            return AgentAction(
                action_type=ActionType.TOOL_CALL,
                tool_name="list_files",
                tool_input={"path": "."},
                thought_summary="Inspect the project structure first.",
            )

        if step_count == 1:
            return AgentAction(
                action_type=ActionType.TOOL_CALL,
                tool_name="save_note",
                tool_input={
                    "title": "initial_project_inspection",
                    "content": "The Agent listed the project files as the first inspection step.",
                },
                thought_summary="Save a note about the inspection.",
            )

        return AgentAction(
            action_type=ActionType.FINAL_ANSWER,
            final_answer=(
                "Phase 1 Agent Harness ran successfully. "
                "It listed files, saved a note, recorded traces, and produced this final answer."
            ),
            thought_summary="The minimal workflow is complete.",
        )
