import json
from datetime import datetime
from pathlib import Path
from typing import Any

from pydantic import BaseModel, Field

from research_pilot.core.state import AgentState
from research_pilot.workflows.paper_workflows import PaperWorkflowRunner


class PaperEvalCase(BaseModel):
    """One paper workflow evaluation case."""

    case_id: str
    workflow: str = "paper_answer"
    question: str
    save_report: bool = False
    max_papers: int = 3
    min_sources: int = 3
    force_download: bool = False


class PaperEvalMetrics(BaseModel):
    """Rule-based metrics for a paper workflow result."""

    workflow_success: bool
    no_tool_error: bool
    has_answer_section: bool
    has_architecture_breakdown: bool
    has_sources_used: bool
    has_limitations: bool
    has_citations: bool
    report_saved: bool
    answer_length: int
    num_steps: int
    num_tool_errors: int
    passed: bool


class PaperEvalResult(BaseModel):
    """Evaluation result for one case."""

    case_id: str
    workflow: str
    question: str
    final_answer: str
    metrics: PaperEvalMetrics
    trace_like_steps: list[dict[str, Any]] = Field(default_factory=list)


class PaperEvalSummary(BaseModel):
    """Aggregated evaluation summary."""

    total: int
    passed: int
    failed: int
    pass_rate: float
    results_path: str
    summary_path: str


class PaperWorkflowEvaluator:
    """Evaluate deterministic paper workflows.

    This evaluator does not use an LLM judge yet. It uses stable rule-based
    checks that are useful for regression testing:
    - Did the workflow finish?
    - Did tools fail?
    - Does the answer contain citations?
    - Does it include Sources Used and Limitations?
    """

    def __init__(
        self,
        runner: PaperWorkflowRunner,
        output_dir: Path,
    ):
        self.runner = runner
        self.output_dir = output_dir
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def load_cases(self, cases_path: Path) -> list[PaperEvalCase]:
        cases: list[PaperEvalCase] = []

        with cases_path.open("r", encoding="utf-8") as f:
            for line_no, line in enumerate(f, start=1):
                line = line.strip()

                if not line:
                    continue

                try:
                    payload = json.loads(line)
                    cases.append(PaperEvalCase.model_validate(payload))
                except Exception as exc:
                    raise ValueError(
                        f"Failed to parse eval case at line {line_no}: {exc}"
                    ) from exc

        return cases

    def run_cases(
        self,
        cases: list[PaperEvalCase],
        max_cases: int | None = None,
    ) -> PaperEvalSummary:
        selected_cases = cases[:max_cases] if max_cases else cases

        results: list[PaperEvalResult] = []

        for case in selected_cases:
            print(f"\n[Eval] Running case: {case.case_id}")
            state = self._run_case(case)
            result = self._evaluate_case(case, state)
            results.append(result)

            status = "PASS" if result.metrics.passed else "FAIL"
            print(f"[Eval] {case.case_id}: {status}")

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        results_path = self.output_dir / f"paper_eval_results_{timestamp}.json"
        summary_path = self.output_dir / f"paper_eval_summary_{timestamp}.md"

        results_payload = [result.model_dump() for result in results]
        results_path.write_text(
            json.dumps(results_payload, indent=2, ensure_ascii=False),
            encoding="utf-8",
        )

        passed = sum(1 for result in results if result.metrics.passed)
        total = len(results)
        failed = total - passed
        pass_rate = passed / total if total else 0.0

        summary = PaperEvalSummary(
            total=total,
            passed=passed,
            failed=failed,
            pass_rate=pass_rate,
            results_path=str(results_path),
            summary_path=str(summary_path),
        )

        summary_path.write_text(
            self._render_markdown_summary(summary, results),
            encoding="utf-8",
        )

        return summary

    def _run_case(self, case: PaperEvalCase) -> AgentState:
        if case.workflow == "paper_answer":
            return self.runner.paper_answer(
                question=case.question,
                save_report=case.save_report,
            )

        if case.workflow == "paper_research":
            return self.runner.paper_research(
                question=case.question,
                max_papers=case.max_papers,
                min_sources=case.min_sources,
                force_download=case.force_download,
                save_report=case.save_report,
            )

        raise ValueError(
            f"Unknown workflow: {case.workflow}. "
            "Supported workflows: paper_answer, paper_research."
        )

    def _evaluate_case(self, case: PaperEvalCase, state: AgentState) -> PaperEvalResult:
        answer = state.final_answer or ""

        num_tool_errors = 0
        report_saved = False
        trace_like_steps: list[dict[str, Any]] = []

        for step in state.steps:
            step_payload: dict[str, Any] = {
                "step_id": step.step_id,
                "action_type": str(step.action.action_type),
                "tool_name": step.action.tool_name,
                "observation_success": None,
                "observation_error": None,
            }

            if step.observation is not None:
                step_payload["observation_success"] = step.observation.success
                step_payload["observation_error"] = step.observation.error

                if not step.observation.success:
                    num_tool_errors += 1

                if step.action.tool_name == "save_report" and step.observation.success:
                    report_saved = True

            trace_like_steps.append(step_payload)

        workflow_success = bool(answer.strip())
        no_tool_error = num_tool_errors == 0

        has_answer_section = "## answer" in answer.lower()
        has_architecture_breakdown = "## architecture breakdown" in answer.lower()
        has_sources_used = "## sources used" in answer.lower()
        has_limitations = "## limitations" in answer.lower()

        has_citations = (
            "[source " in answer.lower()
            or "source " in answer.lower()
            or "chunk" in answer.lower()
        )

        answer_length = len(answer)

        passed = all(
            [
                workflow_success,
                no_tool_error,
                has_answer_section,
                has_sources_used,
                has_limitations,
                has_citations,
                answer_length >= 500,
            ]
        )

        if case.save_report:
            passed = passed and report_saved

        metrics = PaperEvalMetrics(
            workflow_success=workflow_success,
            no_tool_error=no_tool_error,
            has_answer_section=has_answer_section,
            has_architecture_breakdown=has_architecture_breakdown,
            has_sources_used=has_sources_used,
            has_limitations=has_limitations,
            has_citations=has_citations,
            report_saved=report_saved,
            answer_length=answer_length,
            num_steps=len(state.steps),
            num_tool_errors=num_tool_errors,
            passed=passed,
        )

        return PaperEvalResult(
            case_id=case.case_id,
            workflow=case.workflow,
            question=case.question,
            final_answer=answer,
            metrics=metrics,
            trace_like_steps=trace_like_steps,
        )

    def _render_markdown_summary(
        self,
        summary: PaperEvalSummary,
        results: list[PaperEvalResult],
    ) -> str:
        lines = [
            "# Paper Workflow Evaluation Summary",
            "",
            f"- Total cases: {summary.total}",
            f"- Passed: {summary.passed}",
            f"- Failed: {summary.failed}",
            f"- Pass rate: {summary.pass_rate:.1%}",
            f"- Results JSON: `{summary.results_path}`",
            "",
            "## Case Results",
            "",
        ]

        for result in results:
            status = "PASS" if result.metrics.passed else "FAIL"

            lines.extend(
                [
                    f"### {result.case_id}: {status}",
                    "",
                    f"- Workflow: `{result.workflow}`",
                    f"- Question: {result.question}",
                    f"- Workflow success: {result.metrics.workflow_success}",
                    f"- No tool error: {result.metrics.no_tool_error}",
                    f"- Has Answer section: {result.metrics.has_answer_section}",
                    f"- Has Architecture Breakdown: {result.metrics.has_architecture_breakdown}",
                    f"- Has Sources Used: {result.metrics.has_sources_used}",
                    f"- Has Limitations: {result.metrics.has_limitations}",
                    f"- Has citations: {result.metrics.has_citations}",
                    f"- Report saved: {result.metrics.report_saved}",
                    f"- Answer length: {result.metrics.answer_length}",
                    f"- Steps: {result.metrics.num_steps}",
                    f"- Tool errors: {result.metrics.num_tool_errors}",
                    "",
                    "#### Answer Preview",
                    "",
                    "```markdown",
                    result.final_answer[:1200],
                    "```",
                    "",
                ]
            )

        return "\n".join(lines)