from dataclasses import dataclass
from pathlib import Path


@dataclass
class PermissionResult:
    allowed: bool
    reason: str = ""


class PermissionChecker:
    """Simple permission checker for file and shell tools.

    The first version is intentionally conservative.
    Later phases can add user confirmation and more fine-grained policies.
    """

    dangerous_shell_keywords = [
        "rm -rf",
        "del /s",
        "format",
        "shutdown",
        "reboot",
        "curl ",
        "wget ",
        "invoke-webrequest",
        "powershell -enc",
    ]

    sensitive_file_keywords = [
        ".env",
        "id_rsa",
        "id_ed25519",
        "token",
        "secret",
        "credential",
    ]

    def __init__(self, workspace: Path):
        self.workspace = workspace.resolve()

    def check_file_path(self, path: str) -> PermissionResult:
        target = Path(path)

        if not target.is_absolute():
            target = Path.cwd() / target

        target = target.resolve()
        lowered = str(target).lower()

        for keyword in self.sensitive_file_keywords:
            if keyword.lower() in lowered:
                return PermissionResult(
                    allowed=False,
                    reason=f"Access denied because the path looks sensitive: {path}",
                )

        return PermissionResult(allowed=True)

    def check_shell_command(self, command: str) -> PermissionResult:
        lowered = command.lower()

        for keyword in self.dangerous_shell_keywords:
            if keyword.lower() in lowered:
                return PermissionResult(
                    allowed=False,
                    reason=f"Command blocked by permission policy: {keyword}",
                )

        return PermissionResult(allowed=True)
