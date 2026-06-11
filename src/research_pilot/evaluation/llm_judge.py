import json
from typing import Any

from pydantic import BaseModel, Field

from research_pilot.core.evidence import EvidenceStore
from research_pilot.core.llm_client import OpenAICompatibleLLMClient


class LLMJudgeScores(BaseModel):
    """Structured LLM judge scores for one paper QA answer."""

    groundedness: int = Field(..., ge=1, le=5)
    citation_quality: int = Field(..., ge=1, le=5)
    completeness: int = Field(..., ge=1, le=5)
    clarity: int = Field(..., ge=1, le=5)
    hallucination_risk: int = Field(..., ge=1, le=5)

    overall_score: float = Field(..., ge=1.0, le=5.0)
    verdict: str
    strengths: list[str] = Field(default_factory=list)
    weaknesses: list[str] = Field(default_factory=list)
    suggestions: list[str] = Field(default_factory=list)


class PaperAnswerLLMJudge:
    """LLM-as-judge evaluator for citation-aware paper answers.

    The judge receives:
    - the original question
    - the final answer
    - the retrieved evidence stored during the workflow

    It returns a structured JSON score.
    """

    def __init__(self, llm_client: OpenAICompatibleLLMClient):
        self.llm_client = llm_client

    def judge(
        self,
        question: str,
        final_answer: str,
        evidence_store: EvidenceStore,
        max_evidence_items: int = 10,
        max_chars_per_item: int = 2500,
    ) -> LLMJudgeScores:
        evidence_text = evidence_store.render(
            max_items=max_evidence_items,
            max_chars_per_item=max_chars_per_item,
        )

        messages = [
            {
                "role": "system",
                "content": self._system_prompt(),
            },
            {
                "role": "user",
                "content": f"""Question:
{question}

Retrieved evidence:
{evidence_text}

Final answer:
{final_answer}
""",
            },
        ]

        raw = self.llm_client.complete(messages)
        payload = self._extract_json(raw)

        return LLMJudgeScores.model_validate(payload)

    def _system_prompt(self) -> str:
        return """You are a strict evaluator for a citation-aware paper QA system.

Your job is to judge whether the final answer is well supported by the retrieved evidence.

Evaluate the answer using these dimensions:

1. groundedness:
- 5: every important claim is clearly supported by retrieved evidence.
- 3: mostly supported, but some claims are weakly supported.
- 1: many claims are unsupported or invented.

2. citation_quality:
- 5: citations are specific, useful, and attached to key claims.
- 3: citations exist but are incomplete or too broad.
- 1: citations are missing, misleading, or not connected to claims.

3. completeness:
- 5: answers the question thoroughly.
- 3: answers the main question but misses important aspects.
- 1: largely incomplete.

4. clarity:
- 5: clear, structured, and easy to understand.
- 3: understandable but somewhat vague.
- 1: confusing or poorly organized.

5. hallucination_risk:
- 5: very low hallucination risk.
- 3: moderate hallucination risk.
- 1: high hallucination risk.

Return JSON only. Do not include markdown fences.

Use this exact schema:

{
  "groundedness": 1-5,
  "citation_quality": 1-5,
  "completeness": 1-5,
  "clarity": 1-5,
  "hallucination_risk": 1-5,
  "overall_score": 1.0-5.0,
  "verdict": "PASS" or "WEAK_PASS" or "FAIL",
  "strengths": ["..."],
  "weaknesses": ["..."],
  "suggestions": ["..."]
}

Be strict. If the answer contains claims that are not supported by the evidence, lower groundedness and hallucination_risk.
"""

    @staticmethod
    def _extract_json(text: str) -> dict[str, Any]:
        text = text.strip()

        if text.startswith("```"):
            lines = text.splitlines()
            lines = [
                line for line in lines
                if not line.strip().startswith("```")
            ]
            text = "\n".join(lines).strip()

        try:
            return json.loads(text)
        except json.JSONDecodeError:
            start = text.find("{")
            end = text.rfind("}")

            if start == -1 or end == -1 or end <= start:
                raise ValueError(f"LLM judge did not return valid JSON: {text}")

            return json.loads(text[start:end + 1])