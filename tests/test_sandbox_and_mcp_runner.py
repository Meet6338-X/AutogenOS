"""
Unit tests for Ephemeral Sandbox, RTK Token Killer, and Code Execution with MCP.
"""

from autogenos.execution.sandbox import ExecutionSandbox
from autogenos.execution.code_runner import MCPCodeRunner
from autogenos.tool_attention.token_killer import TokenKiller


def test_token_killer_compression():
    verbose_log = "\n".join([
        "Requirement already satisfied: pydantic in c:/site-packages",
        "Requirement already satisfied: numpy in c:/site-packages",
        "Requirement already satisfied: typing-extensions in c:/site-packages",
        "[===>        ] 25% downloading package archive...",
        "[============] 100% unpacking package archive...",
        "Traceback (most recent call last):",
        "  File 'main.py', line 12, in <module>",
        "ZeroDivisionError: division by zero",
    ])

    compressed, orig_tok, comp_tok = TokenKiller.compress_terminal_output(verbose_log)
    assert "ZeroDivisionError" in compressed
    assert "RTK:" in compressed
    assert comp_tok < orig_tok


def test_sandbox_python_execution(tmp_path):
    sandbox = ExecutionSandbox(sandbox_dir=tmp_path)
    exit_code, stdout, stderr, stats = sandbox.run_python_code('print("AutogenOS_Execution_Test")')
    assert exit_code == 0
    assert "AutogenOS_Execution_Test" in stdout
    sandbox.cleanup()


def test_mcp_code_runner_single_pass(tmp_path):
    sandbox = ExecutionSandbox(sandbox_dir=tmp_path)
    runner = MCPCodeRunner(sandbox=sandbox)

    test_code = """
import os
test_path = 'verified_output.txt'
with open(test_path, 'w') as f:
    f.write('grounding_data')
record_evidence('FILE_CREATED', {'path': test_path})
"""
    success, summary, evidence = runner.execute_code_as_policy(test_code)
    assert success is True
    assert evidence is not None
    assert evidence.passed is True
    sandbox.cleanup()
