import pytest
import argparse
from unittest.mock import patch, MagicMock
from autogenos.cli.main import cmd_ui, main

def test_cli_ui_command_parsing():
    """Verify 'ui' subcommand arguments parse cleanly."""
    with patch("sys.argv", ["autogenos", "ui", "--port", "3456", "--dev", "--no-open"]):
        with patch("autogenos.cli.main.cmd_ui") as mock_cmd_ui:
            main()
            assert mock_cmd_ui.called
            args = mock_cmd_ui.call_args[0][0]
            assert args.port == 3456
            assert args.dev is True
            assert args.open is False

def test_cmd_ui_invocation_flow():
    """Verify cmd_ui constructs appropriate npm subprocess command."""
    args = argparse.Namespace(port=3000, dev=False, open=False)
    with patch("subprocess.run") as mock_subproc, \
         patch("shutil.which", return_value="npm.cmd"):
        cmd_ui(args)
        assert mock_subproc.called
        called_cmd = mock_subproc.call_args[0][0]
        assert "npm.cmd" in called_cmd[0]
        assert "start" in called_cmd
