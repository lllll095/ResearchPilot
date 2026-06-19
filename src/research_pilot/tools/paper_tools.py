import json
import re
import time
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from datetime import datetime
from pathlib import Path
from typing import Any
import ssl
import certifi

from research_pilot.config import settings
from research_pilot.core.evidence import EvidenceItem, EvidenceType
from research_pilot.core.observation import Observation
from research_pilot.core.tool import BaseTool, ToolSpec


ATOM_NS = {"atom": "http://www.w3.org/2005/Atom"}


def _safe_filename(text: str, max_len: int = 120) -> str:
    text = text.strip().replace("\n", " ")
    text = re.sub(r"\s+", "_", text)
    text = re.sub(r"[^a-zA-Z0-9_\-\.]", "", text)
    return text[:max_len] or "paper"

def _normalize_title(title: str) -> str:
    """Normalize paper title for fallback deduplication."""

    title = title.lower().strip()
    title = re.sub(r"\s+", " ", title)
    title = re.sub(r"[^a-z0-9 ]", "", title)
    return title


def _paper_dedupe_key(paper: dict[str, Any]) -> str:
    """Build a stable dedupe key for a paper.

    Prefer arXiv ID. Fall back to normalized title. Fall back to PDF URL.
    """

    arxiv_id = paper.get("arxiv_id", "").strip()
    if arxiv_id:
        return arxiv_id

    title = paper.get("title", "").strip()
    if title:
        return f"title:{_normalize_title(title)}"

    pdf_url = paper.get("pdf_url", "").strip()
    if pdf_url:
        return f"url:{pdf_url}"

    return ""


def dedupe_papers(papers: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Remove duplicate papers from a list while preserving order."""

    seen: set[str] = set()
    unique: list[dict[str, Any]] = []

    for paper in papers:
        key = _paper_dedupe_key(paper)

        if not key:
            continue

        if key in seen:
            continue

        seen.add(key)
        unique.append(paper)

    return unique


def _load_download_index(index_path: Path) -> dict[str, Any]:
    """Load global paper download index."""

    if not index_path.exists():
        return {}

    try:
        return json.loads(index_path.read_text(encoding="utf-8"))
    except Exception:
        return {}


def _save_download_index(index_path: Path, index: dict[str, Any]) -> None:
    """Save global paper download index."""

    index_path.parent.mkdir(parents=True, exist_ok=True)
    index_path.write_text(
        json.dumps(index, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )

def _get_text(element, path: str) -> str:
    found = element.find(path, ATOM_NS)
    if found is None or found.text is None:
        return ""
    return found.text.strip()

def _urlopen_with_certifi(request, timeout: int = 30):
    """Open HTTPS URL using certifi CA bundle.

    Falls back to default SSL context if certifi is unavailable.
    """

    try:
        context = ssl.create_default_context(cafile=certifi.where())
    except Exception:
        context = ssl.create_default_context()

    try:
        return urllib.request.urlopen(request, timeout=timeout, context=context)
    except ssl.SSLError:
        return urllib.request.urlopen(request, timeout=timeout)

def search_arxiv(query: str, max_results: int = 5) -> list[dict[str, Any]]:
    """Search arXiv via the official Atom API."""

    params = {
        "search_query": f"all:{query}",
        "start": 0,
        "max_results": max_results,
        "sortBy": "relevance",
        "sortOrder": "descending",
    }

    url = "https://export.arxiv.org/api/query?" + urllib.parse.urlencode(params)

    request = urllib.request.Request(
        url,
        headers={
            "User-Agent": "ResearchPilot/0.1 (educational agent project)"
        },
    )

    try:
        with _urlopen_with_certifi(request, timeout=30) as response:
            data = response.read()
    except Exception as exc:
        raise RuntimeError(
            f"Failed to call arXiv API. URL={url}. Original error: {repr(exc)}"
        ) from exc

    root = ET.fromstring(data)
    entries = []

    for entry in root.findall("atom:entry", ATOM_NS):
        title = _get_text(entry, "atom:title")
        summary = _get_text(entry, "atom:summary")
        published = _get_text(entry, "atom:published")
        abs_url = _get_text(entry, "atom:id")

        authors = []
        for author in entry.findall("atom:author", ATOM_NS):
            name = _get_text(author, "atom:name")
            if name:
                authors.append(name)

        pdf_url = ""
        for link in entry.findall("atom:link", ATOM_NS):
            if link.attrib.get("title") == "pdf" or link.attrib.get("type") == "application/pdf":
                pdf_url = link.attrib.get("href", "")
                break

        if not pdf_url and "/abs/" in abs_url:
            arxiv_id = abs_url.rstrip("/").split("/")[-1]
            pdf_url = f"https://arxiv.org/pdf/{arxiv_id}.pdf"

        arxiv_id = abs_url.rstrip("/").split("/")[-1] if abs_url else ""

        entries.append(
            {
                "arxiv_id": arxiv_id,
                "title": " ".join(title.split()),
                "authors": authors,
                "published": published,
                "abstract": " ".join(summary.split()),
                "abs_url": abs_url,
                "pdf_url": pdf_url,
            }
        )

    return entries


class ArxivPaperSearchTool(BaseTool):
    name = "paper_search"
    description = "Search arXiv papers for a query and save paper metadata as evidence."

    def spec(self) -> ToolSpec:
        return ToolSpec(
            name=self.name,
            description=self.description,
            input_schema={
                "query": "Paper search query.",
                "max_results": "Optional number of results. Default is 5.",
            },
        )

    def run(self, tool_input: dict, state=None) -> Observation:
        query = tool_input.get("query", "")
        max_results = int(tool_input.get("max_results", 5))

        if not query:
            return Observation(
                success=False,
                content="Missing input: query",
                error="MissingQuery",
            )

        try:
            papers = dedupe_papers(search_arxiv(query=query, max_results=max_results))
        except Exception as exc:
            return Observation(
                success=False,
                content=f"arXiv search failed: {exc}",
                error="ArxivSearchFailed",
            )

        content = self._format_papers(query, papers)

        if state is not None:
            state.evidence_store.add(
                EvidenceItem(
                    evidence_type=EvidenceType.PAPER,
                    source=f"arxiv_search:{query}",
                    content=content,
                    metadata={
                        "query": query,
                        "num_results": len(papers),
                        "papers": papers,
                    },
                )
            )

        return Observation(
            success=True,
            content=content,
            metadata={
                "query": query,
                "num_results": len(papers),
                "papers": papers,
            },
        )

    @staticmethod
    def _format_papers(query: str, papers: list[dict[str, Any]]) -> str:
        lines = [f"arXiv paper search results for query: {query}", ""]

        if not papers:
            lines.append("No papers found.")
            return "\n".join(lines)

        for idx, paper in enumerate(papers, start=1):
            authors = ", ".join(paper["authors"][:5])
            if len(paper["authors"]) > 5:
                authors += ", et al."

            lines.append(f"{idx}. {paper['title']}")
            lines.append(f"   arXiv ID: {paper['arxiv_id']}")
            lines.append(f"   Authors: {authors}")
            lines.append(f"   Published: {paper['published']}")
            lines.append(f"   Abstract URL: {paper['abs_url']}")
            lines.append(f"   PDF URL: {paper['pdf_url']}")
            lines.append(f"   Abstract: {paper['abstract'][:700]}")
            lines.append("")

        return "\n".join(lines)


class ArxivPaperDownloadTool(BaseTool):
    name = "paper_download"
    description = "Search arXiv and download a limited number of open PDFs into workspace/documents/papers."

    def __init__(self, paper_dir: Path):
        self.paper_dir = paper_dir
        self.paper_dir.mkdir(parents=True, exist_ok=True)

    def spec(self) -> ToolSpec:
        return ToolSpec(
            name=self.name,
            description=self.description,
            input_schema={
                "query": "Paper search query.",
                "max_papers": (
                    "Maximum number of PDFs to download. "
                    f"Hard-capped by MAX_PAPER_DOWNLOADS={settings.max_paper_downloads}."
                ),
            },
        )

    def run(self, tool_input: dict, state=None) -> Observation:
        query = tool_input.get("query", "")
        requested_max = int(tool_input.get("max_papers", settings.max_paper_downloads))
        max_papers = max(1, min(requested_max, settings.max_paper_downloads))

        if not query:
            return Observation(
                success=False,
                content="Missing input: query",
                error="MissingQuery",
            )

        # Search more candidates than needed, because some may already be downloaded.
        candidate_limit = max(max_papers * 5, 10)

        try:
            papers = dedupe_papers(search_arxiv(query=query, max_results=candidate_limit))
        except Exception as exc:
            return Observation(
                success=False,
                content=f"arXiv search failed: {exc}",
                error="ArxivSearchFailed",
            )

        index_path = self.paper_dir / "download_index.json"
        download_index = _load_download_index(index_path)

        run_stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        target_dir = self.paper_dir / run_stamp
        target_dir.mkdir(parents=True, exist_ok=True)

        downloaded = []
        skipped_duplicates = []
        failed = []

        for paper in papers:
            if len(downloaded) >= max_papers:
                break

            key = _paper_dedupe_key(paper)

            if not key:
                failed.append(
                    {
                        "title": paper.get("title", ""),
                        "reason": "Cannot build dedupe key.",
                    }
                )
                continue

            if key in download_index:
                skipped_duplicates.append(
                    {
                        "title": paper.get("title", ""),
                        "arxiv_id": paper.get("arxiv_id", ""),
                        "reason": "Already downloaded.",
                        "existing_path": download_index[key].get("path", ""),
                    }
                )
                continue

            pdf_url = paper.get("pdf_url")

            if not pdf_url:
                failed.append(
                    {
                        "title": paper.get("title", ""),
                        "reason": "No PDF URL found.",
                    }
                )
                continue

            filename = (
                f"{len(downloaded) + 1:02d}_"
                f"{_safe_filename(paper.get('arxiv_id') or paper.get('title', 'paper'))}.pdf"
            )
            path = target_dir / filename

            try:
                request = urllib.request.Request(
                    pdf_url,
                    headers={
                        "User-Agent": "ResearchPilot/0.1 educational-agent-project"
                    },
                )

                with _urlopen_with_certifi(request, timeout=60) as response:
                    path.write_bytes(response.read())

                item = {
                    "title": paper.get("title", ""),
                    "arxiv_id": paper.get("arxiv_id", ""),
                    "pdf_url": pdf_url,
                    "abs_url": paper.get("abs_url", ""),
                    "path": str(path),
                    "downloaded_at": run_stamp,
                    "dedupe_key": key,
                }

                downloaded.append(item)

                download_index[key] = item
                _save_download_index(index_path, download_index)

                # Be polite to arXiv.
                time.sleep(1)

            except Exception as exc:
                failed.append(
                    {
                        "title": paper.get("title", ""),
                        "pdf_url": pdf_url,
                        "reason": str(exc),
                    }
                )

        manifest = {
            "query": query,
            "max_papers": max_papers,
            "candidate_limit": candidate_limit,
            "downloaded": downloaded,
            "skipped_duplicates": skipped_duplicates,
            "failed": failed,
            "download_index_path": str(index_path),
        }

        manifest_path = target_dir / "manifest.json"
        manifest_path.write_text(
            json.dumps(manifest, indent=2, ensure_ascii=False),
            encoding="utf-8",
        )

        lines = [
            f"Paper download results for query: {query}",
            f"Target directory: {target_dir}",
            f"Downloaded new papers: {len(downloaded)}",
            f"Skipped duplicates: {len(skipped_duplicates)}",
            f"Failed: {len(failed)}",
            f"Download index: {index_path}",
            "",
        ]

        if downloaded:
            lines.append("Downloaded papers:")
            for item in downloaded:
                lines.append(f"- {item['title']}")
                lines.append(f"  arXiv ID: {item['arxiv_id']}")
                lines.append(f"  Path: {item['path']}")
                lines.append("")

        if skipped_duplicates:
            lines.append("Skipped duplicate papers:")
            for item in skipped_duplicates:
                lines.append(f"- {item.get('title', '')}")
                lines.append(f"  arXiv ID: {item.get('arxiv_id', '')}")
                lines.append(f"  Existing path: {item.get('existing_path', '')}")
                lines.append("")

        if failed:
            lines.append("Failed downloads:")
            for item in failed:
                lines.append(f"- {item.get('title', '')}: {item.get('reason', '')}")

        content = "\n".join(lines)

        if state is not None:
            state.evidence_store.add(
                EvidenceItem(
                    evidence_type=EvidenceType.PAPER,
                    source=f"paper_download:{query}",
                    content=content,
                    metadata=manifest,
                )
            )

        return Observation(
            success=True,
            content=content,
            metadata=manifest,
        )
