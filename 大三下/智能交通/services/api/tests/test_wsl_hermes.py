from __future__ import annotations

import asyncio
import subprocess
import unittest
from pathlib import Path
from unittest.mock import AsyncMock, patch

from app.config import settings
from app.models import TaskRecord, TaskState, TaskType
from app.services.hermes import HermesAdapter
from app.services.wsl_bridge import WslConfigurationError, WslPathMapper, verify_wsl_hermes_environment


class WslPathMapperTests(unittest.TestCase):
    def test_windows_path_maps_to_wsl_path(self) -> None:
        mapper = WslPathMapper(Path(r"D:\大三下\智能交通"))
        mapped = mapper.workspace_to_wsl(Path(r"D:\大三下\智能交通\services\api\.task_state"))
        self.assertEqual(mapped, "/mnt/d/大三下/智能交通/services/api/.task_state")

    def test_workspace_override_root_is_used(self) -> None:
        mapper = WslPathMapper(
            Path(r"D:\大三下\智能交通"),
            "/mnt/d/custom/traffic-project",
        )
        mapped = mapper.workspace_to_wsl(Path(r"D:\大三下\智能交通\services\api"))
        self.assertEqual(mapped, "/mnt/d/custom/traffic-project/services/api")


class WslPreflightTests(unittest.TestCase):
    @patch("app.services.wsl_bridge.run_wsl_command")
    @patch("app.services.wsl_bridge.list_wsl_distributions")
    @patch("app.services.wsl_bridge.shutil.which")
    def test_preflight_success(
        self,
        mock_which,
        mock_list_distributions,
        mock_run_wsl_command,
    ) -> None:
        mock_which.return_value = r"C:\Windows\System32\wsl.exe"
        mock_list_distributions.return_value = ["Ubuntu-22.04"]
        mock_run_wsl_command.side_effect = [
            subprocess.CompletedProcess(args=[], returncode=0, stdout="/mnt/d/大三下/智能交通\n", stderr=""),
            subprocess.CompletedProcess(args=[], returncode=0, stdout="/usr/local/bin/hermes\n", stderr=""),
        ]

        report = verify_wsl_hermes_environment(
            wsl_command="wsl.exe",
            distribution="Ubuntu-22.04",
            hermes_command="hermes",
            workspace_windows_root=Path(r"D:\大三下\智能交通"),
            workspace_wsl_root_override="/mnt/d/大三下/智能交通",
            timeout_seconds=10,
        )

        self.assertEqual(report.workspace_wsl_root, "/mnt/d/大三下/智能交通")
        self.assertEqual(report.hermes_resolved_path, "/usr/local/bin/hermes")

    @patch("app.services.wsl_bridge.shutil.which", return_value=None)
    def test_preflight_raises_when_wsl_missing(self, _mock_which) -> None:
        with self.assertRaises(WslConfigurationError):
            verify_wsl_hermes_environment(
                wsl_command="wsl.exe",
                distribution="Ubuntu-22.04",
                hermes_command="hermes",
                workspace_windows_root=Path(r"D:\大三下\智能交通"),
                workspace_wsl_root_override=None,
                timeout_seconds=10,
            )


class FakeProcess:
    def __init__(self, returncode: int = 0, stdout: bytes = b"", stderr: bytes = b"") -> None:
        self.returncode = returncode
        self._stdout = stdout
        self._stderr = stderr

    async def communicate(self) -> tuple[bytes, bytes]:
        return self._stdout, self._stderr

    def kill(self) -> None:
        return None


class HermesAdapterTests(unittest.IsolatedAsyncioTestCase):
    def setUp(self) -> None:
        self.original_enabled = settings.hermes_enabled
        self.original_distribution = settings.hermes_wsl_distribution
        self.original_payload_dir = settings.hermes_payload_dir
        self.original_logs_dir = settings.hermes_logs_dir
        self.original_report_output = settings.report_output_dir
        self.original_audio_output = settings.audio_output_dir
        self.original_summary_output = settings.summary_output_dir

        self.test_root = Path(__file__).resolve().parent / "_tmp"
        self.test_root.mkdir(parents=True, exist_ok=True)
        settings.hermes_payload_dir = self.test_root / "payloads"
        settings.hermes_logs_dir = self.test_root / "logs"
        settings.report_output_dir = self.test_root / "reports"
        settings.audio_output_dir = self.test_root / "audio"
        settings.summary_output_dir = self.test_root / "summaries"
        for path in (
            settings.hermes_payload_dir,
            settings.hermes_logs_dir,
            settings.report_output_dir,
            settings.audio_output_dir,
            settings.summary_output_dir,
        ):
            path.mkdir(parents=True, exist_ok=True)

    def tearDown(self) -> None:
        settings.hermes_enabled = self.original_enabled
        settings.hermes_wsl_distribution = self.original_distribution
        settings.hermes_payload_dir = self.original_payload_dir
        settings.hermes_logs_dir = self.original_logs_dir
        settings.report_output_dir = self.original_report_output
        settings.audio_output_dir = self.original_audio_output
        settings.summary_output_dir = self.original_summary_output

    async def test_fallback_execution_writes_stub_artifact(self) -> None:
        settings.hermes_enabled = False
        adapter = HermesAdapter()
        task = TaskRecord(
            task_id="task-stub",
            task_type=TaskType.report,
            title="stub report",
            state=TaskState.queued,
            payload={"scene_name": "test"},
        )

        result = await adapter.run_task(task)

        self.assertEqual(result["provider"], "stub")
        self.assertTrue(Path(result["artifact_path"]).exists())

    @patch.object(HermesAdapter, "validate_environment")
    @patch("asyncio.create_subprocess_exec")
    async def test_wsl_execution_records_result(
        self,
        mock_create_subprocess_exec,
        mock_validate_environment,
    ) -> None:
        settings.hermes_enabled = True
        settings.hermes_wsl_distribution = "Ubuntu-22.04"
        mock_validate_environment.return_value = {
            "workspace_wsl_root": "/mnt/d/大三下/智能交通",
        }
        mock_create_subprocess_exec.return_value = FakeProcess(
            returncode=0,
            stdout="# Report\n\nGenerated by Hermes".encode("utf-8"),
            stderr=b"",
        )

        adapter = HermesAdapter()
        task = TaskRecord(
            task_id="task-report",
            task_type=TaskType.report,
            title="report task",
            state=TaskState.queued,
            payload={"scene_name": "campus"},
        )

        result = await adapter.run_task(task)

        self.assertEqual(result["provider"], "wsl-hermes")
        self.assertEqual(result["exit_code"], 0)
        self.assertTrue(Path(result["artifact_path"]).exists())
        self.assertTrue(Path(result["task_payload_path"]).exists())
        self.assertTrue(Path(result["task_prompt_path"]).exists())

    @patch.object(HermesAdapter, "validate_environment")
    @patch("asyncio.create_subprocess_exec")
    async def test_wsl_execution_failure_raises(
        self,
        mock_create_subprocess_exec,
        mock_validate_environment,
    ) -> None:
        settings.hermes_enabled = True
        mock_validate_environment.return_value = {
            "workspace_wsl_root": "/mnt/d/大三下/智能交通",
        }
        mock_create_subprocess_exec.return_value = FakeProcess(
            returncode=1,
            stdout=b"",
            stderr=b"hermes failed",
        )

        adapter = HermesAdapter()
        task = TaskRecord(
            task_id="task-fail",
            task_type=TaskType.voice,
            title="voice task",
            state=TaskState.queued,
            payload={"scene_name": "incident"},
        )

        with self.assertRaises(RuntimeError):
            await adapter.run_task(task)


if __name__ == "__main__":
    unittest.main()
