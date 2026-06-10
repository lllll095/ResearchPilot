from pathlib import Path

import typer
from rich.console import Console

from research_pilot.agents.mock_agent import MockAgentPolicy
from research_pilot.config import settings
from research_pilot.core.agent_loop import AgentLoop
from research_pilot.core.context_manager import ContextManager
from research_pilot.core.permission import PermissionChecker
from research_pilot.core.tool_runtime import ToolRuntime
from research_pilot.core.trace import TraceStore
from research_pilot.tools.file_tools import ListFilesTool, ReadFileTool
from research_pilot.tools.note_tool import SaveNoteTool
from research_pilot.tools.shell_tool import ShellTool

app = typer.Typer(help="ResearchPilot command line interface.")
console = Console()


def build_phase1_runtime() -> AgentLoop:
    workspace = Path(settings.workspace)
    workspace.mkdir(parents=True, exist_ok=True)

    permission_checker = PermissionChecker(workspace=workspace)
    tool_runtime = ToolRuntime(permission_checker=permission_checker)

    tool_runtime.register(ListFilesTool(permission_checker))
    tool_runtime.register(ReadFileTool(permission_checker))
    tool_runtime.register(SaveNoteTool(workspace / "notes"))
    tool_runtime.register(ShellTool(permission_checker))

    context_manager = ContextManager()
    trace_store = TraceStore(workspace / "traces")
    policy = MockAgentPolicy()

    return AgentLoop(
        policy=policy,
        tool_runtime=tool_runtime,
        context_manager=context_manager,
        trace_store=trace_store,
        max_steps=5,
    )


@app.command()
def run(goal: str):
    """Run the Phase 1 mock Agent Harness."""

    loop = build_phase1_runtime()
    result = loop.run(goal)

    console.rule("[bold green]Final Answer")
    console.print(result.final_answer)


@app.command()
def tools():
    """List available tools."""

    loop = build_phase1_runtime()
    names = loop.tool_runtime.list_tools()

    console.rule("[bold blue]Available Tools")
    for name in names:
        console.print(f"- {name}")


if __name__ == "__main__":
    app()
