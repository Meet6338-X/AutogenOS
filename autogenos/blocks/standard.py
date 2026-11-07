"""
AutogenOS Standard Built-in Feature Blocks.
Pre-packages core capabilities (Shell, Hash, TTS, Browser, Doctor, Eval, Notifications)
as plug-and-play modular blocks ready for runtime registration.
"""

from __future__ import annotations
import os
import subprocess
import hashlib
from pathlib import Path
from typing import Any, Dict, List, Optional

from autogenos.blocks.base import BaseBlock, BlockType
from autogenos.components.local_tts import LocalTTS
from autogenos.components.browser_agent import WebContentDistiller
from autogenos.core.system_doctor import SystemDoctor
from autogenos.eval.benchmark_harness import BenchmarkHarness
from autogenos.notifications.dispatcher import NotificationDispatcher, NotificationSeverity


class ShellExecutionBlock(BaseBlock):
    """Executes safe shell commands in local workspace."""

    def __init__(self):
        super().__init__(
            block_id="tools.os.exec_shell",
            block_type=BlockType.TOOL,
            name="Shell Execution Block",
            description="Executes a shell command on host OS and returns exit code, stdout, and stderr.",
            tags=["shell", "terminal", "system"]
        )

    async def execute(self, command: str, cwd: Optional[str] = None, timeout: float = 30.0) -> Dict[str, Any]:
        res = subprocess.run(
            command,
            shell=True,
            capture_output=True,
            text=True,
            cwd=cwd,
            timeout=timeout
        )
        return {
            "exit_code": res.returncode,
            "stdout": res.stdout,
            "stderr": res.stderr,
            "success": res.returncode == 0
        }


class FileHashVerificationBlock(BaseBlock):
    """Computes exact SHA-256 digest of target files for deterministic environmental proof."""

    def __init__(self):
        super().__init__(
            block_id="tools.verify.file_hash",
            block_type=BlockType.TOOL,
            name="File Hash Verification Block",
            description="Computes and verifies SHA-256 hash of a file on disk.",
            tags=["verification", "sha256", "grounding"]
        )

    async def execute(self, file_path: str) -> Dict[str, Any]:
        p = Path(file_path)
        if not p.exists() or not p.is_file():
            return {"exists": False, "sha256": None, "error": f"File not found: {file_path}"}

        h = hashlib.sha256()
        with open(p, "rb") as f:
            while chunk := f.read(8192):
                h.update(chunk)

        digest = h.hexdigest()
        return {"exists": True, "sha256": digest, "size_bytes": p.stat().st_size}


class OfflineTTSBlock(BaseBlock):
    """100% free, zero-cloud speech synthesizer using offline audio drivers."""

    def __init__(self):
        super().__init__(
            block_id="actions.voice.local_tts",
            block_type=BlockType.ACTION,
            name="Offline Speech Synthesis Block",
            description="Synthesizes voice audio locally with zero latency using SAPI5/Piper.",
            tags=["voice", "speech", "tts"]
        )
        self.tts = LocalTTS()

    async def execute(self, text: str, asynchronous: bool = True) -> Dict[str, Any]:
        success = self.tts.speak(text, asynchronous=asynchronous)
        return {"spoken_text": text, "success": success}


class BrowserScraperBlock(BaseBlock):
    """Distills complex web DOM into token-efficient Markdown with interactive element maps."""

    def __init__(self):
        super().__init__(
            block_id="perception.browser.distill",
            block_type=BlockType.PERCEPTION,
            name="Browser DOM Distillation Block",
            description="Distills web pages into token-efficient Markdown and extracts clickable selectors.",
            tags=["browser", "cdp", "scraping"]
        )

    async def execute(self, html: Optional[str] = None, url: Optional[str] = None) -> Dict[str, Any]:
        raw_html = html
        if not raw_html and url:
            import httpx
            resp = httpx.get(url, timeout=10.0, follow_redirects=True, headers={"User-Agent": "Mozilla/5.0"})
            raw_html = resp.text

        raw_html = raw_html or "<html><body>Empty</body></html>"
        md = WebContentDistiller.html_to_markdown(raw_html)
        elements = WebContentDistiller.extract_interactive_elements(raw_html)
        return {
            "markdown": md,
            "interactive_elements_count": len(elements),
            "elements": [e.model_dump() for e in elements[:10]]
        }


class SystemDoctorBlock(BaseBlock):
    """Executes full diagnostic suite across OS bridges, MCP tools, and storage."""

    def __init__(self):
        super().__init__(
            block_id="diagnostics.system.doctor",
            block_type=BlockType.EVAL,
            name="System Doctor Block",
            description="Performs end-to-end diagnostic checks across all host subsystems.",
            tags=["doctor", "diagnostics", "health"]
        )
        self.doctor = SystemDoctor()

    async def execute(self) -> Dict[str, Any]:
        report = self.doctor.run_diagnostics()
        return report.model_dump()


class BenchmarkEvalBlock(BaseBlock):
    """Executes empirical benchmark suites (OSWorld, Agent-Diff, Tool Attention)."""

    def __init__(self):
        super().__init__(
            block_id="eval.benchmarks.harness",
            block_type=BlockType.EVAL,
            name="Benchmark Evaluation Harness Block",
            description="Runs empirical benchmarks and outputs deterministic composite scores.",
            tags=["eval", "benchmark", "osworld"]
        )
        self.harness = BenchmarkHarness()

    async def execute(self, suite: str = "all") -> Dict[str, Any]:
        if suite == "all":
            report = self.harness.run_all()
            return report.model_dump()
        else:
            res = self.harness.run_suite(suite)
            return res.model_dump()


class NotificationAlertBlock(BaseBlock):
    """Dispatches mission alerts to native desktop toasts and webhooks."""

    def __init__(self):
        super().__init__(
            block_id="actions.notifications.dispatcher",
            block_type=BlockType.ACTION,
            name="Notification Alert Block",
            description="Dispatches desktop toasts and webhook alerts.",
            tags=["notifications", "alert", "webhook"]
        )
        self.dispatcher = NotificationDispatcher()

    async def execute(
        self,
        title: str,
        body: str,
        severity: str = "INFO",
        channels: Optional[List[str]] = None,
        webhook_url: Optional[str] = None
    ) -> Dict[str, Any]:
        res = self.dispatcher.dispatch(
            title=title,
            body=body,
            severity=severity,
            channels=channels or ["desktop"],
            webhook_url=webhook_url
        )
        return {"dispatched": True, "results": res}


class MeetingJoinerBlock(BaseBlock):
    """Autonomous meeting connector that parses, launches, and joins Google Meet, Zoom, or Teams sessions."""

    def __init__(self):
        super().__init__(
            block_id="actions.meeting.joiner",
            block_type=BlockType.ACTION,
            name="Meeting Joiner Block",
            description="Autonomous meeting connector that joins Google Meet, Zoom, or Teams calls.",
            tags=["action", "meeting", "google-meet", "zoom", "teams"]
        )

    async def execute(
        self,
        url: str,
        display_name: str = "Meet Shah",
        mute_mic: bool = True,
        disable_camera: bool = False,
        auto_join: bool = True,
        browser: str = "auto"
    ) -> Dict[str, Any]:
        from autogenos.components.meeting_agent import MeetingAgent, MeetingConfig
        cfg = MeetingConfig(
            url=url,
            display_name=display_name,
            mute_mic=mute_mic,
            disable_camera=disable_camera,
            auto_join=auto_join,
            browser=browser
        )
        res = await MeetingAgent.join_meeting_fast(cfg)
        return res.model_dump()
