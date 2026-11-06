"""
Ephemeral Execution Sandbox.
Provides isolated execution of synthesized Python/Bash scripts with strict timeouts,
working directory isolation, environment variable scrubbing, and RTK output compression.
"""

from __future__ import annotations
import os
import sys
import tempfile
import subprocess
import logging
from pathlib import Path
from typing import Dict, Optional, Tuple
from autogenos.tool_attention.token_killer import TokenKiller

logger = logging.getLogger("autogenos.sandbox")


class ExecutionSandbox:
    """
    Executes Python and Shell payloads in an isolated directory with timeout
    and resource safety controls.
    """

    def __init__(
        self,
        sandbox_dir: Optional[str | Path] = None,
        default_timeout_seconds: float = 30.0,
        allowed_env_vars: Optional[list[str]] = None
    ):
        self.sandbox_dir = Path(sandbox_dir) if sandbox_dir else Path(tempfile.mkdtemp(prefix="autogenos_sb_"))
        self.sandbox_dir.mkdir(parents=True, exist_ok=True)
        self.timeout = default_timeout_seconds
        self.allowed_env = allowed_env_vars or ["PATH", "SYSTEMROOT", "TEMP", "TMP", "USERNAME", "USER"]

    def _sanitize_env(self, custom_env: Optional[Dict[str, str]] = None) -> Dict[str, str]:
        """Constructs scrubbed environment without leaking host secrets."""
        safe_env = {k: os.environ[k] for k in self.allowed_env if k in os.environ}
        if custom_env:
            safe_env.update(custom_env)
        return safe_env

    def run_command(
        self,
        command: str,
        timeout: Optional[float] = None,
        custom_env: Optional[Dict[str, str]] = None
    ) -> Tuple[int, str, str, Dict[str, int]]:
        """
        Executes a shell command inside the sandbox.
        Returns: (exit_code, compressed_stdout, compressed_stderr, token_stats)
        """
        t = timeout or self.timeout
        env = self._sanitize_env(custom_env)

        try:
            proc = subprocess.run(
                command,
                shell=True,
                cwd=str(self.sandbox_dir),
                capture_output=True,
                text=True,
                timeout=t,
                env=env
            )
            exit_code = proc.returncode
            raw_out = proc.stdout or ""
            raw_err = proc.stderr or ""
        except subprocess.TimeoutExpired:
            return -1, "", f"ExecutionTimedOut after {t} seconds", {"tokens_saved": 0}
        except Exception as e:
            return -1, "", f"ExecutionFailed: {str(e)}", {"tokens_saved": 0}

        # Apply RTK output compression
        comp_out, orig_out_tokens, comp_out_tokens = TokenKiller.compress_terminal_output(raw_out)
        comp_err, orig_err_tokens, comp_err_tokens = TokenKiller.compress_terminal_output(raw_err)

        tokens_saved = (orig_out_tokens + orig_err_tokens) - (comp_out_tokens + comp_err_tokens)

        return exit_code, comp_out, comp_err, {
            "original_tokens": orig_out_tokens + orig_err_tokens,
            "compressed_tokens": comp_out_tokens + comp_err_tokens,
            "tokens_saved": max(0, tokens_saved)
        }

    def run_python_code(
        self,
        code: str,
        timeout: Optional[float] = None,
        injected_vars: Optional[Dict[str, str]] = None
    ) -> Tuple[int, str, str, Dict[str, int]]:
        """Writes Python script to sandbox and executes via current interpreter."""
        script_path = self.sandbox_dir / "exec_payload.py"
        script_path.write_text(code, encoding="utf-8")

        cmd = f'"{sys.executable}" "{script_path.name}"'
        return self.run_command(cmd, timeout=timeout, custom_env=injected_vars)

    def cleanup(self) -> None:
        """Removes temporary sandbox directory."""
        import shutil
        if self.sandbox_dir.exists():
            shutil.rmtree(self.sandbox_dir, ignore_errors=True)
