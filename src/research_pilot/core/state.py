from pydantic import BaseModel, Field

from research_pilot.core.action import AgentAction
from research_pilot.core.observation import Observation


class AgentStep(BaseModel):
    """One step in the Agent loop."""

    step_id: int
    action: AgentAction
    observation: Observation | None = None


class AgentState(BaseModel):
    """State maintained by the Agent loop."""

    user_goal: str
    steps: list[AgentStep] = Field(default_factory=list)
    notes: list[str] = Field(default_factory=list)
    final_answer: str | None = None

    def add_step(self, step: AgentStep) -> None:
        self.steps.append(step)

    def add_note(self, note: str) -> None:
        self.notes.append(note)
