"""
Unit tests for the AutogenOS Unified CLI Suite.
Verifies all subcommands: mcp-tools, mcp-call, self-train, browser, status, papers, tool-attention, doctor, eval, train.
"""

import sys
import pytest
from unittest.mock import patch
from autogenos.cli.main import main


def test_cli_version(capsys):
    with pytest.raises(SystemExit) as exc_info:
        with patch.object(sys, "argv", ["autogenos", "--version"]):
            main()
    assert exc_info.value.code == 0
    captured = capsys.readouterr()
    assert "0.1.0" in captured.out or "0.1.0" in captured.err


def test_cli_mcp_tools(capsys):
    with patch.object(sys, "argv", ["autogenos", "mcp-tools"]):
        main()
    captured = capsys.readouterr()
    assert "AutogenOS Model Context Protocol (MCP) Tools Catalog" in captured.out
    assert "autogenos_list_windows" in captured.out
    assert "autogenos_exec_shell" in captured.out


def test_cli_mcp_call(capsys):
    with patch.object(sys, "argv", ["autogenos", "mcp-call", "autogenos_exec_shell", "--args", '{"command": "echo CLI_TEST_PASSED"}']):
        main()
    captured = capsys.readouterr()
    assert "[SUCCESS]" in captured.out
    assert "CLI_TEST_PASSED" in captured.out


def test_cli_self_train_report(capsys):
    with patch.object(sys, "argv", ["autogenos", "self-train", "--rules"]):
        main()
    captured = capsys.readouterr()
    assert "AUTOGENOS AUTONOMOUS SELF-TRAINING REPORT" in captured.out
    assert "Trajectories Recorded" in captured.out


def test_cli_tool_attention(capsys):
    with patch.object(sys, "argv", ["autogenos", "tool-attention", "Inspect windows and click buttons", "--top-k", "2"]):
        main()
    captured = capsys.readouterr()
    assert "Active Promoted Tools" in captured.out
    assert "MCP TAX ELIMINATION METRICS" in captured.out


def test_cli_status(capsys):
    with patch.object(sys, "argv", ["autogenos", "status"]):
        main()
    captured = capsys.readouterr()
    assert "AUTOGENOS HOST ENVIRONMENT" in captured.out
    assert "Accessibility Bridge" in captured.out


def test_cli_papers(capsys):
    with patch.object(sys, "argv", ["autogenos", "papers"]):
        main()
    captured = capsys.readouterr()
    assert "AUTOGENOS ACADEMIC WHITE PAPERS" in captured.out


def test_cli_papers_pdf(capsys):
    with patch.object(sys, "argv", ["autogenos", "papers", "--pdf"]):
        main()
    captured = capsys.readouterr()
    assert "AUTOGENOS OFFICIAL IEEE RESEARCH PAPER" in captured.out
    assert "Meet Shah, Senior Member, IEEE" in captured.out
    assert "VERIFIED" in captured.out


def test_cli_doctor(capsys):
    with patch.object(sys, "argv", ["autogenos", "doctor"]):
        main()
    captured = capsys.readouterr()
    assert "AUTOGENOS SYSTEM DOCTOR DIAGNOSTIC REPORT" in captured.out
    assert "Overall Health" in captured.out


def test_cli_eval(capsys):
    with patch.object(sys, "argv", ["autogenos", "eval"]):
        main()
    captured = capsys.readouterr()
    assert "AUTOGENOS EMPIRICAL BENCHMARK EVALUATION REPORT" in captured.out
    assert "Final Benchmark Verdict" in captured.out


def test_cli_train(capsys, tmp_path):
    out_dir = str(tmp_path / "cli_train_adapter")
    with patch.object(sys, "argv", ["autogenos", "train", "--epochs", "2", "--adapter-out", out_dir]):
        main()
    captured = capsys.readouterr()
    assert "FINE-TUNING EXECUTION REPORT" in captured.out
    assert "[COMPLETED]" in captured.out
