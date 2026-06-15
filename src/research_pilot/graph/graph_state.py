# src/research_pilot/graph/graph_state.py

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


class GraphStepRecord(BaseModel):
    """One executed graph node step."""

    step_id: int
    node_name: str
    success: bool
    next_node: str | None = None
    is_final: bool = False
    error: str | None = None
    created_at: str = Field(default_factory=lambda: datetime.now().isoformat())
    output_preview: str = ""
    metadata: dict[str, Any] = Field(default_factory=dict)


class GraphState(BaseModel):
    """Shared state object for graph workflow execution.

    This is the graph-level state, not the same as AgentState.

    AgentState:
        one agent/tool execution run

    GraphState:
        one graph workflow execution, with node transitions and shared metadata
    """

    user_request: str

    current_node: str | None = None
    final_answer: str = ""
    is_final: bool = False

    step_count: int = 0
    max_steps: int = 20

    visited_nodes: list[str] = Field(default_factory=list)
    step_records: list[GraphStepRecord] = Field(default_factory=list)

    metadata: dict[str, Any] = Field(default_factory=dict)
    errors: list[str] = Field(default_factory=list)

    created_at: str = Field(default_factory=lambda: datetime.now().isoformat())
    updated_at: str = Field(default_factory=lambda: datetime.now().isoformat())

    def add_step_record(self, record: GraphStepRecord) -> None:
        self.step_records.append(record)
        self.visited_nodes.append(record.node_name)
        self.step_count += 1
        self.updated_at = datetime.now().isoformat()

    def add_error(self, error: str) -> None:
        self.errors.append(error)
        self.updated_at = datetime.now().isoformat()

    def set_final_answer(self, answer: str) -> None:
        self.final_answer = answer
        self.is_final = True
        self.updated_at = datetime.now().isoformat()