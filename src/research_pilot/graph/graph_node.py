# src/research_pilot/graph/graph_node.py

from abc import ABC, abstractmethod
from collections.abc import Callable
from typing import Any

from pydantic import BaseModel, Field

from research_pilot.graph.graph_state import GraphState


class GraphNodeResult(BaseModel):
    """Result returned by one graph node."""

    success: bool = True

    # If next_node is set, GraphWorkflowRunner will route to it.
    # If it is None, the runner uses default or conditional edges.
    next_node: str | None = None

    # If is_final=True, graph execution stops.
    is_final: bool = False
    final_answer: str = ""

    # Updates are merged into GraphState.metadata by default.
    updates: dict[str, Any] = Field(default_factory=dict)

    # Extra metadata for tracing/debugging.
    metadata: dict[str, Any] = Field(default_factory=dict)

    error: str | None = None
    output_preview: str = ""


class BaseGraphNode(ABC):
    """Base class for all graph workflow nodes."""

    name: str = "base_node"
    description: str = "Base graph node."

    @abstractmethod
    def run(self, state: GraphState) -> GraphNodeResult:
        """Run this node against the shared graph state."""


class FunctionGraphNode(BaseGraphNode):
    """Wrap a normal Python function as a graph node."""

    def __init__(
        self,
        name: str,
        fn: Callable[[GraphState], GraphNodeResult],
        description: str = "",
    ):
        self.name = name
        self.fn = fn
        self.description = description or f"Function graph node: {name}"

    def run(self, state: GraphState) -> GraphNodeResult:
        return self.fn(state)