from pathlib import Path

from research_pilot.agents.mock_agent import MockAgentPolicy
from research_pilot.core.agent_loop import AgentLoop
from research_pilot.core.context_manager import ContextManager
from research_pilot.core.permission import PermissionChecker
from research_pilot.core.tool_runtime import ToolRuntime
from research_pilot.core.trace import TraceStore
from research_pilot.tools.file_tools import ListFilesTool
from research_pilot.tools.note_tool import SaveNoteTool


def test_phase1_agent_loop_runs(tmp_path: Path):
    permission_checker = PermissionChecker(workspace=tmp_path)
    tool_runtime = ToolRuntime(permission_checker=permission_checker)

    tool_runtime.register(ListFilesTool(permission_checker))
    tool_runtime.register(SaveNoteTool(tmp_path / "notes"))

    loop = AgentLoop(
        policy=MockAgentPolicy(),
        tool_runtime=tool_runtime,
        context_manager=ContextManager(),
        trace_store=TraceStore(tmp_path / "traces"),
        max_steps=5,
    )

    result = loop.run("analyze this project")

    assert result.final_answer is not None
    assert len(result.steps) >= 3
