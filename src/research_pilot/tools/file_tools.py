from pathlib import Path

from research_pilot.core.observation import Observation
from research_pilot.core.permission import PermissionChecker
from research_pilot.core.tool import BaseTool, ToolSpec


class ListFilesTool(BaseTool):
    name = "list_files"
    description = "List files and folders under a directory."

    def __init__(self, permission_checker: PermissionChecker):
        self.permission_checker = permission_checker

    def spec(self) -> ToolSpec:
        return ToolSpec(
            name=self.name,
            description=self.description,
            input_schema={
                "path": "Directory path to list. Use '.' for the current project root."
            },
        )

    def run(self, tool_input: dict, state=None) -> Observation:
        path = tool_input.get("path", ".")
        permission = self.permission_checker.check_file_path(path)

        if not permission.allowed:
            return Observation(
                success=False,
                content=permission.reason,
                error="PermissionDenied",
            )

        target = Path(path)

        if not target.exists():
            return Observation(
                success=False,
                content=f"Path does not exist: {path}",
                error="PathNotFound",
            )

        if not target.is_dir():
            return Observation(
                success=False,
                content=f"Path is not a directory: {path}",
                error="NotADirectory",
            )

        items = []
        for item in sorted(target.iterdir()):
            suffix = "/" if item.is_dir() else ""
            items.append(f"{item.name}{suffix}")

        content = "\n".join(items) if items else "(empty directory)"

        return Observation(
            success=True,
            content=content,
            metadata={"path": str(target)},
        )

class ReadFileTool(BaseTool):
    name = "read_file"
    description = "Read a text file. For PDF files, extract limited text when possible."

    def __init__(self, permission_checker):
        self.permission_checker = permission_checker

    def spec(self) -> ToolSpec:
        return ToolSpec(
            name=self.name,
            description=self.description,
            input_schema={
                "path": "Path to the file to read. Supports absolute path, project-root relative path, or workspace-relative path.",
                "max_chars": "Optional maximum number of characters to return. Default is 4000.",
                "max_pdf_pages": "Optional maximum number of PDF pages to extract. Default is 3.",
            },
        )

    def run(self, tool_input: dict, state=None) -> Observation:
        raw_path = tool_input.get("path", "")
        max_chars = int(tool_input.get("max_chars", 4000))
        max_pdf_pages = int(tool_input.get("max_pdf_pages", 3))

        if not raw_path:
            return Observation(
                success=False,
                content="Missing input: path",
                error="MissingPath",
            )

        path, tried_paths = self._resolve_input_path(raw_path)

        if not self.permission_checker.check_file_path(path):
            return Observation(
                success=False,
                content=f"Path is not allowed: {path}",
                error="PermissionDenied",
            )

        if not path.exists():
            return Observation(
                success=False,
                content=(
                    f"File does not exist: {path}\n\n"
                    f"Tried paths:\n" + "\n".join(f"- {p}" for p in tried_paths)
                ),
                error="FileNotFound",
            )

        if path.is_dir():
            return Observation(
                success=False,
                content=f"Path is a directory, not a file: {path}",
                error="IsDirectory",
            )

        if path.suffix.lower() == ".pdf":
            return self._read_pdf(path, max_chars=max_chars, max_pages=max_pdf_pages)

        return self._read_text_or_binary_metadata(path, max_chars=max_chars)

    def _resolve_input_path(self, raw_path: str) -> tuple[Path, list[str]]:
        """Resolve user-provided path robustly.

        Supported:
        - Absolute path
        - Project-root relative path: workspace/documents/...
        - Workspace-relative path: documents/...
        """

        raw = Path(raw_path)
        workspace = self.permission_checker.workspace.resolve()

        candidates: list[Path] = []

        if raw.is_absolute():
            candidates.append(raw.resolve())
        else:
            candidates.append((Path.cwd() / raw).resolve())
            candidates.append((workspace / raw).resolve())

        tried = [str(path) for path in candidates]

        for candidate in candidates:
            if candidate.exists():
                return candidate, tried

        return candidates[0], tried

    def _read_text_or_binary_metadata(self, path: Path, max_chars: int) -> Observation:
        try:
            content = path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            return Observation(
                success=True,
                content=(
                    f"The file appears to be binary or not UTF-8 text.\n"
                    f"Path: {path}\n"
                    f"Size: {path.stat().st_size} bytes\n"
                    f"This file should not be read as plain text."
                ),
                metadata={
                    "path": str(path),
                    "size_bytes": path.stat().st_size,
                    "binary": True,
                },
            )

        if len(content) > max_chars:
            content = content[:max_chars] + "\n\n[File content truncated]"

        return Observation(
            success=True,
            content=content,
            metadata={
                "path": str(path),
                "size_bytes": path.stat().st_size,
                "binary": False,
            },
        )

    def _read_pdf(self, path: Path, max_chars: int, max_pages: int) -> Observation:
        try:
            from pypdf import PdfReader
        except ImportError:
            return Observation(
                success=True,
                content=(
                    f"This is a PDF file and it was downloaded successfully.\n"
                    f"Path: {path}\n"
                    f"Size: {path.stat().st_size} bytes\n\n"
                    f"PDF text extraction is not available because pypdf is not installed.\n"
                    f"Run: pip install pypdf"
                ),
                metadata={
                    "path": str(path),
                    "size_bytes": path.stat().st_size,
                    "file_type": "pdf",
                    "text_extracted": False,
                },
            )

        try:
            reader = PdfReader(str(path))
            total_pages = len(reader.pages)
            pages_to_read = min(max_pages, total_pages)

            chunks = []

            for page_idx in range(pages_to_read):
                page_text = reader.pages[page_idx].extract_text() or ""
                chunks.append(f"\n--- Page {page_idx + 1} ---\n{page_text}")

            content = "\n".join(chunks).strip()

            if not content:
                content = (
                    f"This PDF was downloaded successfully, but no extractable text "
                    f"was found in the first {pages_to_read} pages.\n"
                    f"Path: {path}"
                )

            if len(content) > max_chars:
                content = content[:max_chars] + "\n\n[PDF text truncated]"

            return Observation(
                success=True,
                content=content,
                metadata={
                    "path": str(path),
                    "size_bytes": path.stat().st_size,
                    "file_type": "pdf",
                    "total_pages": total_pages,
                    "pages_read": pages_to_read,
                    "text_extracted": bool(content.strip()),
                },
            )

        except Exception as exc:
            return Observation(
                success=True,
                content=(
                    f"This PDF was downloaded successfully, but text extraction failed.\n"
                    f"Path: {path}\n"
                    f"Size: {path.stat().st_size} bytes\n"
                    f"Reason: {exc}\n\n"
                    f"The file can still be used later by the Paper RAG indexing pipeline."
                ),
                metadata={
                    "path": str(path),
                    "size_bytes": path.stat().st_size,
                    "file_type": "pdf",
                    "text_extracted": False,
                    "extract_error": repr(exc),
                },
            )