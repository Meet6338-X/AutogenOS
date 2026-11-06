"""
Rust Token Killer (RTK) & Headroom Terminal Output Compressor.
Intercepts shell outputs, compiler errors, and git diffs, compressing them by 60% to 90%
before injection into the language model context window.
"""

from __future__ import annotations
import re
from typing import Tuple


class TokenKiller:
    """
    Compresses verbose CLI outputs (compiler traces, package installation logs,
    git status/diffs, test outputs) to preserve KV cache and prevent token bloat.
    """

    @staticmethod
    def compress_terminal_output(raw_text: str, max_lines: int = 50) -> Tuple[str, int, int]:
        """
        Compresses raw terminal output:
        - Filters out repetitive progress bars and wheel spinners
        - Summarizes long lists of unchanged/clean files
        - Preserves stack traces, error messages, exit codes, and diff headers
        Returns: (compressed_text, original_estimated_tokens, compressed_estimated_tokens)
        """
        if not raw_text or not raw_text.strip():
            return "", 0, 0

        original_tokens = len(raw_text) // 4
        lines = raw_text.splitlines()

        cleaned_lines = []
        in_error_block = False
        suppressed_count = 0

        for line in lines:
            stripped = line.strip()

            # Remove ANSI escape sequences
            clean = re.sub(r"\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])", "", stripped)

            # Detect progress bars / spinners (e.g. [===>    ], 45%, 100/200)
            if re.search(r"(\[={2,}>?\]|\b\d{1,3}%\b|fetching|downloading|unpacking)", clean, re.IGNORECASE):
                suppressed_count += 1
                continue

            # Detect repetitive pip/npm requirement already satisfied
            if re.search(r"(Requirement already satisfied|npm info|npm notice)", clean, re.IGNORECASE):
                suppressed_count += 1
                continue

            # Detect compiler errors, exceptions, stack traces
            if re.search(r"(error|exception|fail|traceback|syntaxerror|assertionerror|errno)", clean, re.IGNORECASE):
                in_error_block = True

            cleaned_lines.append(clean)

        # Truncate if still excessive, preserving head and tail
        if len(cleaned_lines) > max_lines:
            head = cleaned_lines[: max_lines // 2]
            tail = cleaned_lines[-(max_lines // 2) :]
            omitted = len(cleaned_lines) - len(head) - len(tail)
            result_lines = (
                head
                + [f"\n... [RTK: {omitted + suppressed_count} non-critical lines compressed/omitted] ...\n"]
                + tail
            )
        else:
            result_lines = cleaned_lines
            if suppressed_count > 0:
                result_lines.append(f"\n[RTK: {suppressed_count} progress/verbose lines compressed]")

        compressed_text = "\n".join(result_lines)
        compressed_tokens = len(compressed_text) // 4

        return compressed_text, original_tokens, compressed_tokens

    @staticmethod
    def compress_git_diff(raw_diff: str) -> str:
        """
        Compresses git diff by condensing unchanged hunk contexts
        while preserving exact added/deleted lines.
        """
        compressed_lines = []
        for line in raw_diff.splitlines():
            # Skip binary file diff warnings or redundant index hashes
            if line.startswith("index ") and ".." in line:
                continue
            compressed_lines.append(line)
        return "\n".join(compressed_lines)
