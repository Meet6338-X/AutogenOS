"""
High-Performance Local Terminal Execution Component.
Executes shell commands with real-time output capture, timeout enforcement,
and automatic RTK terminal output token compression.
"""

from __future__ import annotations
import os
import subprocess
import logging
from pathlib import Path
from typing import Dict, Optional, Tuple, Any
from autogenos.tool_attention.token_killer import TokenKiller

logger = logging.getLogger("autogenos.terminal_runner")


class TerminalRunner:
    """
    Executes native shell commands with streaming output, exit code tracking,
    and automatic RTK token compression.
    """

    def __init__(self, default_cwd: Optional[str | Path] = None, timeout_seconds: float = 60.0):
        self.default_cwd = Path(default_cwd).resolve() if default_cwd else Path.cwd()
        self.timeout = timeout_seconds

    def execute(
        self,
        command: str,
        cwd: Optional[str | Path] = None,
        timeout: Optional[float] = None,
        env: Optional[Dict[str, str]] = None
    ) -> Dict[str, Any]:
        """
        Runs command synchronously and returns structured execution payload.
        """
        run_cwd = str(Path(cwd).resolve()) if cwd else str(self.default_cwd)
        run_timeout = timeout or self.timeout
        run_env = os.environ.copy()
        if env:
            run_env.update(env)

        logger.info(f"Executing CLI command in {run_cwd}: {command}")

        try:
            proc = subprocess.run(
                command,
                shell=True,
                cwd=run_cwd,
                capture_output=True,
                text=True,
                timeout=run_timeout,
                env=run_env
            )
            exit_code = proc.returncode
            raw_stdout = proc.stdout or ""
            raw_stderr = proc.stderr or ""
            timed_out = False
        except subprocess.TimeoutExpired as e:
            exit_code = -1
            raw_stdout = e.stdout or "" if hasattr(e, "stdout") and e.stdout else ""
            raw_stderr = f"Process timed out after {run_timeout} seconds"
            timed_out = True
        except Exception as e:
            exit_code = -1
            raw_stdout = ""
            raw_stderr = f"Execution error: {str(e)}"
            timed_out = False

        # Apply RTK compression
        comp_stdout, orig_out_tok, comp_out_tok = TokenKiller.compress_terminal_output(raw_stdout)
        comp_stderr, orig_err_tok, comp_err_tok = TokenKiller.compress_terminal_output(raw_stderr)

        return {
            "command": command,
            "exit_code": exit_code,
            "success": exit_code == 0,
            "timed_out": timed_out,
            "stdout": comp_stdout,
            "stderr": comp_stderr,
            "original_tokens": orig_out_tok + orig_err_tok,
            "compressed_tokens": comp_out_tok + comp_err_tok,
            "tokens_saved": max(0, (orig_out_tok + orig_err_tok) - (comp_out_tok + comp_err_tok)),
            "cwd": run_cwd
        }
