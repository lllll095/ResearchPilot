import json
from datetime import datetime
from pathlib import Path
from typing import Any

from pydantic import BaseModel, Field

from research_pilot.core.state import AgentState
from research_pilot.workflows.code_workflows import CodeWorkflowRunner


class CodeEvalCase(BaseModel):
    """One codebase QA evaluation case."""

    case_id: str
    question: str
    path: str = "src/research_pilot"
    required_terms: list[str] = Field(default_factory=list)
    required_files: list[str] = Field(default_factory=list)
    min_answer_chars: int = 300


class CodeEvalMetrics(BaseModel):
    """Rule-based code answer metrics."""

    workflow_success: bool
    no_tool_errors: bool
    has_answer_section: bool
    has_code_flow_section: bool
    has_key_files_section: bool
    has_evidence_section: bool
    has_limitations_section: bool
    has_required_terms: bool
    has_required_files: bool
    answer_long_enough: bool
    num_steps: int
    num_tool_errors: int
    missing_terms: list[str] = Field(default_factory=list)
    missing_files: list[str] = Field(default_factory=list)

    @property
    def passed(self) -> bool:
        return all(
            [
                self.workflow_success,
                self.no_tool_errors,
                self.has_answer_section,
                self.has_code_flow_section,
                self.has_key_files_section,
                self.has_evidence_section,
                self.has_limitations_section,
                self.has_required_terms,
                self.has_required_files,
                self.answer_long_enough,
            ]
        )


class CodeEvalResult(BaseModel):
    """Evaluation result for one code QA case."""

    case_id: str
    question: str
    final_answer: str
    metrics: CodeEvalMetrics
    trace_like_steps: list[dict[str, Any]] = Field(default_factory=list)


class CodeEvalSummary(BaseModel):
    """Summary of a code evaluation run."""

    total: int
    passed: int
    failed: int
    pass_rate: float
    results_path: str
    summary_path: str


class CodeWorkflowEvaluator:
    """Evaluate deterministic code-answer workflow."""

    def __init__(
        self,
        runner: CodeWorkflowRunner,
        output_dir: Path,
    ):
        self.runner = runner
        self.output_dir = output_dir
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def load_cases(self, cases_path: Path) -> list[CodeEvalCase]:
        cases: list[CodeEvalCase] = []

        with cases_path.open("r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()

                if not line:
                    continue

                cases.append(CodeEvalCase.model_validate_json(line))

        return cases

    def run_cases(
        self,
        cases: list[CodeEvalCase],
        max_cases: int | None = None,
    ) -> CodeEvalSummary:
        if max_cases is not None:
            cases = cases[:max_cases]

        results: list[CodeEvalResult] = []

        for case in cases:
            print(f"[CodeEval] Running case: {case.case_id}")

            result = self._evaluate_case(case)
            results.append(result)

            status = "PASS" if result.metrics.passed else "FAIL"
            print(f"[CodeEval] {case.case_id}: {status}")

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

        results_path = self.output_dir / f"code_eval_results_{timestamp}.json"
        summary_path = self.output_dir / f"code_eval_summary_{timestamp}.md"

        results_payload = [result.model_dump() for result in results]

        results_path.write_text(
            json.dumps(results_payload, indent=2, ensure_ascii=False),
            encoding="utf-8",
        )

        summary_md = self._render_markdown_summary(results)
        summary_path.write_text(summary_md, encoding="utf-8")

        total = len(results)
        passed = sum(1 for result in results if result.metrics.passed)
        failed = total - passed
        pass_rate = passed / total if total else 0.0

        return CodeEvalSummary(
            total=total,
            passed=passed,
            failed=failed,
            pass_rate=pass_rate,
            results_path=str(results_path),
            summary_path=str(summary_path),
        )

    def _evaluate_case(self, case: CodeEvalCase) -> CodeEvalResult:
        state = self.runner.code_answer(
            question=case.question,
            path=case.path,
            max_results=20,
            max_files_to_read=3,
        )

        answer = state.final_answer or ""

        trace_like_steps = self._extract_trace_like_steps(state)

        num_tool_errors = 0

        for step in state.steps:
            obs = step.observation
            if obs is not None and not obs.success:
                num_tool_errors += 1

        workflow_success = bool(answer.strip()) and "failed during" not in answer.lower()
        no_tool_errors = num_tool_errors == 0

        answer_lower = answer.lower()
        answer_normalized = answer.replace("/", "\\").lower()

        missing_terms = [
            term
            for term in case.required_terms
            if term.lower() not in answer_lower
        ]

        missing_files = [
            file
            for file in case.required_files
            if file.replace("/", "\\").lower() not in answer_normalized
        ]

        metrics = CodeEvalMetrics(
            workflow_success=workflow_success,
            no_tool_errors=no_tool_errors,
            has_answer_section="## answer" in answer_lower,
            has_code_flow_section="## code flow" in answer_lower,
            has_key_files_section="## key files" in answer_lower,
            has_evidence_section="## evidence used" in answer_lower,
            has_limitations_section="## limitations" in answer_lower,
            has_required_terms=len(missing_terms) == 0,
            has_required_files=len(missing_files) == 0,
            answer_long_enough=len(answer) >= case.min_answer_chars,
            num_steps=len(state.steps),
            num_tool_errors=num_tool_errors,
            missing_terms=missing_terms,
            missing_files=missing_files,
        )

        return CodeEvalResult(
            case_id=case.case_id,
            question=case.question,
            final_answer=answer,
            metrics=metrics,
            trace_like_steps=trace_like_steps,
        )

    @staticmethod
    def _extract_trace_like_steps(state: AgentState) -> list[dict[str, Any]]:
        trace_steps: list[dict[str, Any]] = []

        for step in state.steps:
            action = step.action
            observation = step.observation

            trace_steps.append(
                {
                    "step_id": step.step_id,
                    "action_type": str(action.action_type),
                    "tool_name": action.tool_name,
                    "tool_input": action.tool_input,
                    "observation_success": (
                        observation.success if observation is not None else None
                    ),
                    "observation_error": (
                        observation.error if observation is not None else None
                    ),
                }
            )

        return trace_steps

    def _render_markdown_summary(self, results: list[CodeEvalResult]) -> str:
        lines = [
            "# Code Workflow Evaluation Summary",
            "",
            f"Total cases: {len(results)}",
            f"Passed: {sum(1 for result in results if result.metrics.passed)}",
            f"Failed: {sum(1 for result in results if not result.metrics.passed)}",
            "",
            "---",
            "",
        ]

        for result in results:
            status = "PASS" if result.metrics.passed else "FAIL"
            metrics = result.metrics

            lines.extend(
                [
                    f"## {result.case_id}: {status}",
                    "",
                    f"Question: `{result.question}`",
                    "",
                    "### Metrics",
                    "",
                    f"- Workflow success: {metrics.workflow_success}",
                    f"- No tool errors: {metrics.no_tool_errors}",
                    f"- Has Answer section: {metrics.has_answer_section}",
                    f"- Has Code Flow section: {metrics.has_code_flow_section}",
                    f"- Has Key Files section: {metrics.has_key_files_section}",
                    f"- Has Evidence Used section: {metrics.has_evidence_section}",
                    f"- Has Limitations section: {metrics.has_limitations_section}",
                    f"- Has required terms: {metrics.has_required_terms}",
                    f"- Has required files: {metrics.has_required_files}",
                    f"- Answer long enough: {metrics.answer_long_enough}",
                    f"- Number of steps: {metrics.num_steps}",
                    f"- Number of tool errors: {metrics.num_tool_errors}",
                    "",
                ]
            )

            if metrics.missing_terms:
                lines.append(f"Missing terms: {metrics.missing_terms}")
                lines.append("")

            if metrics.missing_files:
                lines.append(f"Missing files: {metrics.missing_files}")
                lines.append("")

            lines.extend(
                [
                    "### Answer Preview",
                    "",
                    "```markdown",
                    result.final_answer[:2000],
                    "```",
                    "",
                    "---",
                    "",
                ]
            )

        return "\n".join(lines)