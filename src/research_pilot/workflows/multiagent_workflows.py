# src/research_pilot/workflows/multiagent_workflows.py

from rich.console import Console

from research_pilot.conversation.session import ConversationSession
from research_pilot.core.llm_client import OpenAICompatibleLLMClient
from research_pilot.core.state import AgentState
from research_pilot.multiagent import ResearchPilotBlackboard, SubAgentInput
from research_pilot.multiagent.subagents import (
    CodeSubAgent,
    PaperSubAgent,
    PlannerSubAgent,
    ReviewerSubAgent,
    WriterSubAgent,
)
from research_pilot.workflows.code_workflows import CodeWorkflowRunner
from research_pilot.workflows.paper_workflows import PaperWorkflowRunner


class MultiAgentWorkflowRunner:
    """Minimal multi-agent workflow runner.

    Current flow:

        blackboard
          -> LLM PlannerSubAgent
          -> CodeSubAgent or PaperSubAgent
          -> final answer

    This version validates the subagent and blackboard architecture before
    adding WriterSubAgent and ReviewerSubAgent.
    """

    def __init__(
        self,
        code_workflow_runner: CodeWorkflowRunner,
        paper_workflow_runner: PaperWorkflowRunner,
        llm_client: OpenAICompatibleLLMClient,
        console: Console | None = None,
        max_specialist_retries: int = 1,
    ):
        self.code_workflow_runner = code_workflow_runner
        self.paper_workflow_runner = paper_workflow_runner
        self.llm_client = llm_client
        self.console = console or Console()
        self.max_specialist_retries = max_specialist_retries

        self.planner = PlannerSubAgent(llm_client=self.llm_client)
        self.code_agent = CodeSubAgent(runner=self.code_workflow_runner)
        self.paper_agent = PaperSubAgent(runner=self.paper_workflow_runner)
        self.reviewer = ReviewerSubAgent(llm_client=self.llm_client)
        self.writer = WriterSubAgent(llm_client=self.llm_client)

    def answer(
        self,
        user_request: str,
        session: ConversationSession | None = None,
    ) -> AgentState:
        """Run the multi-agent workflow and return an AgentState.

        Flow:
            planner
            -> specialist
            -> reviewer
            -> optional specialist retry
            -> optional writer rewrite
        """

        blackboard = ResearchPilotBlackboard.from_session(
            user_request=user_request,
            session=session,
        )

        planner_output = self.planner.run(
            SubAgentInput(
                blackboard=blackboard,
                instruction=user_request,
            )
        )

        decision = planner_output.updates.get("planner_decision", {})
        next_agent = decision.get("next_agent")

        source_agent = "none"

        if next_agent == "code":
            source_agent = "code"
        elif next_agent == "paper":
            source_agent = "paper"

        if source_agent in {"code", "paper"}:
            specialist_output = self._run_specialist(
                source_agent=source_agent,
                user_request=user_request,
                blackboard=blackboard,
                decision=decision,
            )

            final_answer = self._answer_from_specialist_output(
                specialist_output=specialist_output,
                source_agent=source_agent,
            )
        else:
            specialist_output = None
            final_answer = (
                "The multi-agent runner could not select a specialized subagent.\n\n"
                "Current available subagents: code, paper.\n\n"
                f"Planner decision:\n{planner_output.content}"
            )

        review_output = self._run_reviewer(
            blackboard=blackboard,
            candidate_answer=final_answer,
            source_agent=source_agent,
        )

        retry_outputs = []
        retry_review_outputs = []

        review_result = review_output.updates.get("review_result", {})

        if (
            source_agent in {"code", "paper"}
            and not review_result.get("passed", True)
            and self.max_specialist_retries > 0
        ):
            retry_instruction = self._build_retry_instruction(
                user_request=user_request,
                review_result=review_result,
                previous_answer=final_answer,
            )

            for retry_idx in range(self.max_specialist_retries):
                retry_output = self._run_specialist(
                    source_agent=source_agent,
                    user_request=retry_instruction,
                    blackboard=blackboard,
                    decision=decision,
                )
                retry_outputs.append(retry_output)

                retry_answer = self._answer_from_specialist_output(
                    specialist_output=retry_output,
                    source_agent=source_agent,
                )

                retry_review_output = self._run_reviewer(
                    blackboard=blackboard,
                    candidate_answer=retry_answer,
                    source_agent=source_agent,
                )
                retry_review_outputs.append(retry_review_output)

                retry_review_result = retry_review_output.updates.get("review_result", {})

                final_answer = retry_answer
                review_output = retry_review_output
                review_result = retry_review_result

                if retry_review_result.get("passed", False):
                    break

        writer_output = None

        if not review_result.get("passed", True):
            writer_output = self._run_writer(
                blackboard=blackboard,
                candidate_answer=final_answer,
                review_result=review_result,
                source_agent=source_agent,
            )

            if writer_output.success and writer_output.content.strip():
                final_answer = writer_output.content

        state = AgentState(user_goal=user_request)
        state.final_answer = final_answer

        self._attach_metadata(
            state=state,
            key="blackboard",
            value=blackboard.model_dump(),
        )
        self._attach_metadata(
            state=state,
            key="planner_output",
            value=planner_output.model_dump(),
        )
        self._attach_metadata(
            state=state,
            key="initial_specialist_output",
            value=specialist_output.model_dump() if specialist_output is not None else None,
        )
        self._attach_metadata(
            state=state,
            key="review_output",
            value=review_output.model_dump(),
        )
        self._attach_metadata(
            state=state,
            key="specialist_retry_outputs",
            value=[output.model_dump() for output in retry_outputs],
        )
        self._attach_metadata(
            state=state,
            key="specialist_retry_review_outputs",
            value=[output.model_dump() for output in retry_review_outputs],
        )

        if writer_output is not None:
            self._attach_metadata(
                state=state,
                key="writer_output",
                value=writer_output.model_dump(),
            )

        return state
    
    def _run_specialist(
        self,
        source_agent: str,
        user_request: str,
        blackboard: ResearchPilotBlackboard,
        decision: dict,
    ):
        """Run the selected specialist subagent."""

        if source_agent == "code":
            return self.code_agent.run(
                SubAgentInput(
                    blackboard=blackboard,
                    instruction=user_request,
                    metadata={
                        "planner_decision": decision,
                    },
                )
            )

        if source_agent == "paper":
            return self.paper_agent.run(
                SubAgentInput(
                    blackboard=blackboard,
                    instruction=user_request,
                    metadata={
                        "planner_decision": decision,
                    },
                )
            )

        raise ValueError(f"Unknown specialist agent: {source_agent}")

    def _run_code_agent(
        self,
        user_request: str,
        blackboard: ResearchPilotBlackboard,
        decision: dict,
    ) -> str:
        code_output = self.code_agent.run(
            SubAgentInput(
                blackboard=blackboard,
                instruction=user_request,
                metadata={
                    "planner_decision": decision,
                },
            )
        )

        if not code_output.success:
            return (
                "CodeSubAgent failed.\n\n"
                f"{code_output.error}"
            )

        return code_output.content

    def _run_paper_agent(
        self,
        user_request: str,
        blackboard: ResearchPilotBlackboard,
        decision: dict,
    ) -> str:
        paper_output = self.paper_agent.run(
            SubAgentInput(
                blackboard=blackboard,
                instruction=user_request,
                metadata={
                    "planner_decision": decision,
                },
            )
        )

        if not paper_output.success:
            return (
                "PaperSubAgent failed.\n\n"
                f"{paper_output.error}"
            )

        return paper_output.content

    def _run_reviewer(
        self,
        blackboard: ResearchPilotBlackboard,
        candidate_answer: str,
        source_agent: str,
    ):
        """Run ReviewerSubAgent on the candidate answer.

        The first version records review results but does not rewrite the answer.
        """

        return self.reviewer.run(
            SubAgentInput(
                blackboard=blackboard,
                instruction="Review the candidate answer.",
                metadata={
                    "candidate_answer": candidate_answer,
                    "source_agent": source_agent,
                },
            )
        )

    def _run_writer(
        self,
        blackboard: ResearchPilotBlackboard,
        candidate_answer: str,
        review_result: dict,
        source_agent: str,
    ):
        """Run WriterSubAgent once when review fails."""

        return self.writer.run(
            SubAgentInput(
                blackboard=blackboard,
                instruction="Rewrite the candidate answer using reviewer feedback.",
                metadata={
                    "candidate_answer": candidate_answer,
                    "review_result": review_result,
                    "source_agent": source_agent,
                },
            )
        )

    @staticmethod
    def _attach_metadata(
        state: AgentState,
        key: str,
        value,
    ) -> None:
        """Attach metadata only if AgentState supports metadata."""

        if hasattr(state, "metadata") and isinstance(state.metadata, dict):
            state.metadata[key] = value

    @staticmethod
    def _answer_from_specialist_output(
        specialist_output,
        source_agent: str,
    ) -> str:
        """Convert specialist output into a candidate final answer."""

        if not specialist_output.success:
            return (
                f"{source_agent.capitalize()}SubAgent failed.\n\n"
                f"{specialist_output.error}"
            )

        return specialist_output.content
    
    @staticmethod
    def _build_retry_instruction(
        user_request: str,
        review_result: dict,
        previous_answer: str,
    ) -> str:
        """Build a retry instruction for the same specialist.

        The retry asks the specialist to improve evidence collection or answer
        grounding according to the reviewer feedback.
        """

        issues = review_result.get("issues") or []
        missing_evidence = review_result.get("missing_evidence") or []
        unsupported_claims = review_result.get("unsupported_claims") or []
        suggestions = review_result.get("suggestions") or []

        return f"""Original user request:
    {user_request}

    The previous answer did not pass review.

    Reviewer issues:
    {issues}

    Missing evidence:
    {missing_evidence}

    Unsupported claims:
    {unsupported_claims}

    Reviewer suggestions:
    {suggestions}

    Previous answer:
    {previous_answer}

    Retry instruction:
    Run the specialist workflow again. Try to collect stronger evidence if possible.
    For code tasks, preserve exact class/function/file names and search for the relevant implementation.
    For paper tasks, preserve exact research topic terms and use retrieved paper evidence.
    If the evidence is still insufficient, clearly state the limitation in the final answer.
    """