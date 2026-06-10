import json
from datetime import datetime
from pathlib import Path
from typing import Any

from research_pilot.core.state import AgentState, AgentStep


class TraceStore:
    """Save Agent execution traces to disk."""

    def __init__(self, trace_dir: Path):
        self.trace_dir = trace_dir
        self.trace_dir.mkdir(parents=True, exist_ok=True)

    def save_step(self, run_id: str, step: AgentStep) -> None:
        run_dir = self.trace_dir / run_id
        run_dir.mkdir(parents=True, exist_ok=True)

        step_path = run_dir / f"step_{step.step_id:03d}.json"
        step_path.write_text(
            json.dumps(step.model_dump(), indent=2, ensure_ascii=False, default=str),
            encoding="utf-8",
        )

    def save_final_state(self, run_id: str, state: AgentState) -> Path:
        run_dir = self.trace_dir / run_id
        run_dir.mkdir(parents=True, exist_ok=True)

        final_path = run_dir / "final_state.json"
        payload: dict[str, Any] = state.model_dump()
        payload["saved_at"] = datetime.now().isoformat()

        final_path.write_text(
            json.dumps(payload, indent=2, ensure_ascii=False, default=str),
            encoding="utf-8",
        )

        return final_path
