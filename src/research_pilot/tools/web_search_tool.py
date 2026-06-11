from typing import Any

from research_pilot.config import settings
from research_pilot.core.evidence import EvidenceItem, EvidenceType
from research_pilot.core.observation import Observation
from research_pilot.core.tool import BaseTool, ToolSpec


class MockWebSearchTool(BaseTool):
    """A mock web search tool.

    This is used when no real search provider is configured.
    """

    name = "web_search"
    description = "Search web resources for a query. Uses mock results if no real backend is configured."

    def spec(self) -> ToolSpec:
        return ToolSpec(
            name=self.name,
            description=self.description,
            input_schema={
                "query": "Search query string.",
                "max_results": "Optional number of results. Default is 3.",
            },
        )

    def run(self, tool_input: dict, state=None) -> Observation:
        query = tool_input.get("query", "")
        max_results = int(tool_input.get("max_results", 3))

        if not query:
            return Observation(
                success=False,
                content="Missing input: query",
                error="MissingQuery",
            )

        mock_results = [
            {
                "title": f"Overview of {query}",
                "url": "https://example.com/overview",
                "snippet": (
                    f"{query} is commonly discussed in relation to planning, "
                    "tool use, retrieval, evaluation, and iterative refinement."
                ),
            },
            {
                "title": f"Architectures related to {query}",
                "url": "https://example.com/architecture",
                "snippet": (
                    "A typical agentic architecture includes a planner, executor, "
                    "tool runtime, memory, reflection, and report generation."
                ),
            },
            {
                "title": f"Challenges of {query}",
                "url": "https://example.com/challenges",
                "snippet": (
                    "Common challenges include hallucination control, source grounding, "
                    "tool reliability, context management, and evaluation."
                ),
            },
        ][:max_results]

        content = self._format_results(query=query, results=mock_results, backend="mock")

        self._save_evidence(
            state=state,
            query=query,
            content=content,
            results=mock_results,
            backend="mock",
        )

        return Observation(
            success=True,
            content=content,
            metadata={
                "query": query,
                "num_results": len(mock_results),
                "backend": "mock",
                "results": mock_results,
            },
        )

    @staticmethod
    def _format_results(query: str, results: list[dict[str, Any]], backend: str) -> str:
        lines = [f"Web search results for query: {query}", f"Backend: {backend}", ""]

        for idx, result in enumerate(results, start=1):
            lines.append(f"{idx}. {result.get('title', '(no title)')}")
            lines.append(f"   URL: {result.get('url', '')}")
            lines.append(f"   Snippet: {result.get('snippet', '')}")
            lines.append("")

        return "\n".join(lines)

    @staticmethod
    def _save_evidence(
        state,
        query: str,
        content: str,
        results: list[dict[str, Any]],
        backend: str,
    ) -> None:
        if state is None:
            return

        state.evidence_store.add(
            EvidenceItem(
                evidence_type=EvidenceType.WEB_SEARCH,
                source=f"web_search:{query}",
                content=content,
                metadata={
                    "query": query,
                    "num_results": len(results),
                    "backend": backend,
                    "results": results,
                },
            )
        )


class TavilyWebSearchTool(MockWebSearchTool):
    """A real Tavily-backed web search tool.

    It keeps the same public tool name: web_search.
    """

    name = "web_search"
    description = "Search web resources using Tavily if configured; otherwise use mock results."

    def __init__(self, api_key: str | None = None):
        self.api_key = api_key or settings.tavily_api_key

    def run(self, tool_input: dict, state=None) -> Observation:
        if not self.api_key:
            fallback = MockWebSearchTool()
            observation = fallback.run(tool_input, state=state)
            observation.metadata["fallback_reason"] = "TAVILY_API_KEY is not set."
            return observation

        query = tool_input.get("query", "")
        max_results = int(tool_input.get("max_results", 3))

        if not query:
            return Observation(
                success=False,
                content="Missing input: query",
                error="MissingQuery",
            )

        try:
            from tavily import TavilyClient
        except ImportError:
            fallback = MockWebSearchTool()
            observation = fallback.run(tool_input, state=state)
            observation.metadata["fallback_reason"] = (
                "tavily-python is not installed. Run: pip install -e .[search]"
            )
            return observation

        try:
            client = TavilyClient(api_key=self.api_key)
            response = client.search(
                query=query,
                max_results=max_results,
                search_depth="basic",
                include_answer=False,
            )
        except Exception as exc:
            fallback = MockWebSearchTool()
            observation = fallback.run(tool_input, state=state)
            observation.metadata["fallback_reason"] = f"Tavily search failed: {exc}"
            return observation

        raw_results = response.get("results", [])

        results: list[dict[str, Any]] = []
        for item in raw_results[:max_results]:
            results.append(
                {
                    "title": item.get("title", ""),
                    "url": item.get("url", ""),
                    "snippet": item.get("content", ""),
                    "score": item.get("score"),
                }
            )

        content = self._format_results(query=query, results=results, backend="tavily")

        self._save_evidence(
            state=state,
            query=query,
            content=content,
            results=results,
            backend="tavily",
        )

        return Observation(
            success=True,
            content=content,
            metadata={
                "query": query,
                "num_results": len(results),
                "backend": "tavily",
                "results": results,
            },
        )