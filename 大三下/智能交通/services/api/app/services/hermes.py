from __future__ import annotations

import asyncio
import json
from pathlib import Path

from app.config import settings
from app.models import TaskRecord
from app.services.wsl_bridge import WslConfigurationError, WslPathMapper, verify_wsl_hermes_environment


class HermesAdapter:
    def __init__(self) -> None:
        self._path_mapper = WslPathMapper(
            settings.hermes_workspace_root,
            settings.hermes_wsl_workspace_root,
        )

    def validate_environment(self) -> dict | None:
        if not settings.hermes_enabled:
            return None

        if not settings.hermes_wsl_enabled:
            raise WslConfigurationError("Hermes is enabled, but WSL-backed Hermes execution is disabled.")

        report = verify_wsl_hermes_environment(
            wsl_command=settings.hermes_wsl_command,
            distribution=settings.hermes_wsl_distribution,
            hermes_command=settings.hermes_command,
            workspace_windows_root=settings.hermes_workspace_root,
            workspace_wsl_root_override=settings.hermes_wsl_workspace_root,
            timeout_seconds=min(settings.hermes_timeout_seconds, 30),
        )
        return {
            "provider": "wsl-hermes",
            "wsl_command": report.wsl_command,
            "wsl_distribution": report.distribution,
            "workspace_windows_root": report.workspace_windows_root,
            "workspace_wsl_root": report.workspace_wsl_root,
            "available_distributions": report.available_distributions,
            "hermes_resolved_path": report.hermes_resolved_path,
        }

    async def run_task(self, task: TaskRecord) -> dict:
        if not settings.hermes_enabled:
            return self._fallback_result(task)

        environment = self.validate_environment()
        prepared = self._prepare_task_payload(task)
        prompt = prepared["prompt"]
        artifact_path = prepared["artifact_path"]

        wsl_workspace_root = self._path_mapper.workspace_to_wsl(settings.hermes_workspace_root)
        args = [settings.hermes_wsl_command]
        if settings.hermes_wsl_distribution:
            args.extend(["-d", settings.hermes_wsl_distribution])
        args.extend(
            [
                "--cd",
                wsl_workspace_root,
                settings.hermes_command,
                "chat",
                "-Q",
                "--yolo",
                "-q",
                prompt,
            ]
        )

        process = await asyncio.create_subprocess_exec(
            *args,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )

        try:
            stdout, stderr = await asyncio.wait_for(process.communicate(), timeout=settings.hermes_timeout_seconds)
        except TimeoutError as exc:
            process.kill()
            await process.communicate()
            raise RuntimeError(
                f"WSL Hermes task timed out after {settings.hermes_timeout_seconds} seconds."
            ) from exc

        stdout_text = stdout.decode("utf-8", errors="ignore").strip()
        stderr_text = stderr.decode("utf-8", errors="ignore").strip()

        if process.returncode != 0:
            raise RuntimeError(
                f"WSL Hermes execution failed with exit code {process.returncode}: {stderr_text or stdout_text or 'no output'}"
            )

        artifact_path.write_text(stdout_text, encoding="utf-8")
        log_path = settings.hermes_logs_dir / f"{task.task_id}.log"
        log_path.write_text(
            json.dumps(
                {
                    "args": args,
                    "stdout": stdout_text,
                    "stderr": stderr_text,
                    "returncode": process.returncode,
                },
                ensure_ascii=False,
                indent=2,
            ),
            encoding="utf-8",
        )

        return {
            "provider": "wsl-hermes",
            "message": f"Task executed through WSL Hermes ({task.task_type.value}).",
            "artifact_path": artifact_path.as_posix(),
            "task_payload_path": prepared["payload_path"].as_posix(),
            "task_prompt_path": prepared["prompt_path"].as_posix(),
            "log_path": log_path.as_posix(),
            "stdout": stdout_text,
            "stderr": stderr_text,
            "exit_code": process.returncode,
            "wsl_distribution": settings.hermes_wsl_distribution,
            "wsl_workspace_root": environment["workspace_wsl_root"] if environment else None,
        }

    def _fallback_result(self, task: TaskRecord) -> dict:
        artifact_path = self._artifact_path_for(task)
        artifact_path.write_text(
            self._fallback_content_for(task),
            encoding="utf-8",
        )
        return {
            "provider": "stub",
            "message": "Hermes is disabled; returning simulated task output.",
            "artifact_path": artifact_path.as_posix(),
        }

    def _prepare_task_payload(self, task: TaskRecord) -> dict[str, Path | str]:
        task_dir = settings.hermes_payload_dir / task.task_type.value / task.task_id
        task_dir.mkdir(parents=True, exist_ok=True)

        payload_path = task_dir / "payload.json"
        prompt_path = task_dir / "prompt.txt"
        artifact_path = self._artifact_path_for(task)

        payload_path.write_text(
            json.dumps(
                {
                    "task_id": task.task_id,
                    "task_type": task.task_type.value,
                    "title": task.title,
                    "payload": task.payload,
                    "artifact_path": artifact_path.as_posix(),
                },
                ensure_ascii=False,
                indent=2,
            ),
            encoding="utf-8",
        )

        prompt = self._prompt_for(task, artifact_path)
        prompt_path.write_text(prompt, encoding="utf-8")
        return {
            "payload_path": payload_path,
            "prompt_path": prompt_path,
            "artifact_path": artifact_path,
            "prompt": prompt,
        }

    def _prompt_for(self, task: TaskRecord, artifact_path: Path) -> str:
        payload_json = json.dumps(task.payload, ensure_ascii=False, indent=2)

        if task.task_type.value == "voice":
            return (
                "你是智能交通系统中的语音播报助手。"
                "请基于以下任务信息生成一段简洁、适合中文播报的交通提示稿。"
                "只输出播报正文，不要加解释。\n\n"
                f"任务标题：{task.title}\n"
                f"输出文件：{artifact_path.name}\n"
                f"任务载荷：\n{payload_json}\n"
            )

        if task.task_type.value == "daily-summary":
            return (
                "你是智能交通系统中的运营总结助手。"
                "请根据以下任务信息生成一份 Markdown 格式的每日总结，"
                "包含摘要、重点事件、风险提示和后续建议四部分。\n\n"
                f"任务标题：{task.title}\n"
                f"输出文件：{artifact_path.name}\n"
                f"任务载荷：\n{payload_json}\n"
            )

        return (
            "你是智能交通系统中的报表助手。"
            "请根据以下任务信息生成一份 Markdown 格式的结构化报告，"
            "包含场景概况、关键指标、风险判断和建议动作四部分。\n\n"
            f"任务标题：{task.title}\n"
            f"输出文件：{artifact_path.name}\n"
            f"任务载荷：\n{payload_json}\n"
        )

    def _artifact_path_for(self, task: TaskRecord) -> Path:
        if task.task_type.value == "voice":
            return settings.audio_output_dir / f"{task.task_id}.txt"
        if task.task_type.value == "daily-summary":
            return settings.summary_output_dir / f"{task.task_id}.md"
        return settings.report_output_dir / f"{task.task_id}.md"

    def _fallback_content_for(self, task: TaskRecord) -> str:
        if task.task_type.value == "voice":
            return f"[Stub voice briefing]\n{task.title}\n{json.dumps(task.payload, ensure_ascii=False, indent=2)}\n"
        if task.task_type.value == "daily-summary":
            return f"# Stub Daily Summary\n\n## Title\n{task.title}\n\n## Payload\n```json\n{json.dumps(task.payload, ensure_ascii=False, indent=2)}\n```\n"
        return f"# Stub Report\n\n## Title\n{task.title}\n\n## Payload\n```json\n{json.dumps(task.payload, ensure_ascii=False, indent=2)}\n```\n"
