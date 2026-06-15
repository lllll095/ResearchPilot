# src/research_pilot/graph/demo.py

from research_pilot.graph.graph_node import FunctionGraphNode, GraphNodeResult
from research_pilot.graph.graph_runner import GraphWorkflowRunner
from research_pilot.graph.graph_state import GraphState


def start_node(state: GraphState) -> GraphNodeResult:
    return GraphNodeResult(
        success=True,
        next_node="count",
        updates={
            "counter": 0,
        },
        output_preview="Initialized counter.",
    )


def count_node(state: GraphState) -> GraphNodeResult:
    counter = int(state.metadata.get("counter", 0)) + 1

    if counter >= 3:
        return GraphNodeResult(
            success=True,
            next_node="final",
            updates={
                "counter": counter,
            },
            output_preview=f"Counter reached {counter}; routing to final.",
        )

    return GraphNodeResult(
        success=True,
        next_node="count",
        updates={
            "counter": counter,
        },
        output_preview=f"Counter is {counter}; looping back to count.",
    )


def final_node(state: GraphState) -> GraphNodeResult:
    counter = state.metadata.get("counter", 0)

    return GraphNodeResult(
        success=True,
        is_final=True,
        final_answer=f"Counter demo completed. Final counter value: {counter}",
        output_preview="Final node completed.",
    )


def build_counter_demo_graph() -> GraphWorkflowRunner:
    runner = GraphWorkflowRunner(
        start_node="start",
        max_steps=10,
    )

    runner.add_node(FunctionGraphNode("start", start_node))
    runner.add_node(FunctionGraphNode("count", count_node))
    runner.add_node(FunctionGraphNode("final", final_node))

    return runner


def run_counter_demo() -> GraphState:
    runner = build_counter_demo_graph()
    return runner.run(user_request="Run counter demo.")