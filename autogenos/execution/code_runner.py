"""
Code Execution with MCP: Single-Pass Code-as-Policy Synthesizer and Runner.
Eliminates intermediate conversational turns by compiling multi-step tool calls
into a single executable script executed directly inside the sandbox.
"""

from __future__ import annotations
import textwrap
import logging
from typing import Any, Dict, Optional, Tuple
from autogenos.execution.sandbox import ExecutionSandbox
from autogenos.core.state import DeterministicEvidence, EvidenceType

logger = logging.getLogger("autogenos.code_runner")


class MCPCodeRunner:
    """
    Exposes system capabilities as a pre-populated Python environment.
    Executes generated code in a single pass and extracts deterministic evidence.
    """

    def __init__(self, sandbox: Optional[ExecutionSandbox] = None):
        self.sandbox = sandbox or ExecutionSandbox()

    def generate_harness_template(self, user_code: str) -> str:
        """
        Wraps synthesized agent code with standard telemetry instrumentation,
        error trapping, and JSON evidence emission.
        """
        harness = f'''
import sys
import os
import json
import hashlib

def assert_file_hash(path, expected_hash=None):
    if not os.path.exists(path):
        raise FileNotFoundError(f"File not found: {{path}}")
    h = hashlib.sha256(open(path, "rb").read()).hexdigest()
    if expected_hash and h != expected_hash:
        raise ValueError(f"Hash mismatch: got {{h}}, expected {{expected_hash}}")
    return h

def record_evidence(evidence_type, data):
    payload = {{"type": evidence_type, "data": data}}
    print(f"__AUTOGENOS_EVIDENCE__{{json.dumps(payload)}}__END_EVIDENCE__")

try:
{textwrap.indent(user_code, "    ")}
    print("__AUTOGENOS_SUCCESS__")
except Exception as e:
    import traceback
    traceback.print_exc()
    sys.exit(1)
'''
        return harness

    def execute_code_as_policy(
        self,
        code: str,
        timeout: Optional[float] = 30.0
    ) -> Tuple[bool, str, Optional[DeterministicEvidence]]:
        """
        Runs synthesized code-as-policy and extracts environmental evidence.
        """
        full_script = self.generate_harness_template(code)
        exit_code, stdout, stderr, token_stats = self.sandbox.run_python_code(
            full_script, timeout=timeout
        )

        success = (exit_code == 0) and ("__AUTOGENOS_SUCCESS__" in stdout)
        evidence = None

        if "__AUTOGENOS_EVIDENCE__" in stdout:
            import json
            import re
            match = re.search(r"__AUTOGENOS_EVIDENCE__(.*?)__END_EVIDENCE__", stdout)
            if match:
                try:
                    ev_data = json.loads(match.group(1))
                    evidence = DeterministicEvidence(
                        evidence_type=EvidenceType.SHELL_OUTPUT,
                        source_target="code_as_policy",
                        raw_payload=stdout,
                        passed=success,
                        details=ev_data
                    )
                except Exception:
                    pass

        if not evidence:
            evidence = DeterministicEvidence(
                evidence_type=EvidenceType.SHELL_OUTPUT,
                source_target="sandbox_exec",
                raw_payload=f"exit_code: {exit_code}\nstdout: {stdout}\nstderr: {stderr}",
                passed=success,
                details={"token_stats": token_stats}
            )

        output_summary = stdout if success else f"Error (exit {exit_code}):\n{stderr or stdout}"
        return success, output_summary, evidence
