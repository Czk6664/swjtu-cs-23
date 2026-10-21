from __future__ import annotations

import shutil
import subprocess
from dataclasses import dataclass
from pathlib import Path, PurePosixPath, PureWindowsPath


class WslConfigurationError(RuntimeError):
    """Raised when WSL-backed Hermes cannot be initialized."""


def _clean_wsl_output(value: str) -> str:
    return value.replace("\x00", "").strip()


class WslPathMapper:
    def __init__(self, workspace_root: Path, wsl_workspace_root: str | None = None) -> None:
        self.workspace_root = workspace_root.resolve()
        self.wsl_workspace_root = (
            wsl_workspace_root.rstrip("/") if wsl_workspace_root else self.windows_to_wsl(self.workspace_root)
        )

    def windows_to_wsl(self, value: str | Path) -> str:
        path = Path(value).resolve()
        windows_path = PureWindowsPath(str(path))

        drive = windows_path.drive.rstrip(":").lower()
        if not drive:
            raise WslConfigurationError(f"Cannot map non-drive Windows path to WSL: {path}")

        tail_parts = [part for part in windows_path.parts[1:] if part not in {"\\", "/"}]
        return PurePosixPath("/mnt", drive, *tail_parts).as_posix()

    def workspace_to_wsl(self, value: str | Path) -> str:
        path = Path(value).resolve()
        try:
            relative = path.relative_to(self.workspace_root)
        except ValueError:
            return self.windows_to_wsl(path)

        if not relative.parts:
            return self.wsl_workspace_root
        return PurePosixPath(self.wsl_workspace_root, *relative.parts).as_posix()


@dataclass(slots=True)
class WslPreflightReport:
    wsl_command: str
    distribution: str | None
    workspace_windows_root: str
    workspace_wsl_root: str
    available_distributions: list[str]
    hermes_resolved_path: str


def list_wsl_distributions(wsl_command: str, timeout_seconds: int = 10) -> list[str]:
    result = subprocess.run(
        [wsl_command, "-l", "-q"],
        check=True,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="ignore",
        timeout=timeout_seconds,
    )
    lines = [_clean_wsl_output(line) for line in result.stdout.splitlines()]
    return [line for line in lines if line]


def run_wsl_command(
    *,
    wsl_command: str,
    distribution: str | None,
    cwd: str,
    command: list[str],
    timeout_seconds: int,
) -> subprocess.CompletedProcess[str]:
    args = [wsl_command]
    if distribution:
        args.extend(["-d", distribution])
    args.extend(["--cd", cwd])
    args.extend(command)

    return subprocess.run(
        args,
        check=False,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="ignore",
        timeout=timeout_seconds,
    )


def verify_wsl_hermes_environment(
    *,
    wsl_command: str,
    distribution: str | None,
    hermes_command: str,
    workspace_windows_root: Path,
    workspace_wsl_root_override: str | None,
    timeout_seconds: int,
) -> WslPreflightReport:
    resolved_wsl = shutil.which(wsl_command) or (wsl_command if Path(wsl_command).exists() else None)
    if resolved_wsl is None:
        raise WslConfigurationError(f"WSL command not found: {wsl_command}")

    mapper = WslPathMapper(workspace_windows_root, workspace_wsl_root_override)
    available_distributions = list_wsl_distributions(resolved_wsl, timeout_seconds)

    if distribution and distribution not in available_distributions:
        joined = ", ".join(available_distributions) if available_distributions else "none"
        raise WslConfigurationError(
            f"Configured WSL distribution '{distribution}' was not found. Available distributions: {joined}"
        )

    workspace_wsl_root = mapper.workspace_to_wsl(workspace_windows_root)
    workspace_check = run_wsl_command(
        wsl_command=resolved_wsl,
        distribution=distribution,
        cwd=workspace_wsl_root,
        command=["bash", "-lc", "pwd"],
        timeout_seconds=timeout_seconds,
    )
    if workspace_check.returncode != 0:
        raise WslConfigurationError(
            "WSL workspace check failed. "
            f"stderr: {_clean_wsl_output(workspace_check.stderr) or '(empty)'}"
        )

    hermes_check = run_wsl_command(
        wsl_command=resolved_wsl,
        distribution=distribution,
        cwd=workspace_wsl_root,
        command=["bash", "-lc", f"command -v {hermes_command}"],
        timeout_seconds=timeout_seconds,
    )
    hermes_resolved_path = _clean_wsl_output(hermes_check.stdout)
    if hermes_check.returncode != 0 or not hermes_resolved_path:
        raise WslConfigurationError(
            f"Hermes command '{hermes_command}' was not found inside WSL distribution "
            f"'{distribution or 'default'}'."
        )

    return WslPreflightReport(
        wsl_command=resolved_wsl,
        distribution=distribution,
        workspace_windows_root=str(workspace_windows_root.resolve()),
        workspace_wsl_root=workspace_wsl_root,
        available_distributions=available_distributions,
        hermes_resolved_path=hermes_resolved_path,
    )
