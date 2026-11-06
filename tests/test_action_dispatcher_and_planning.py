"""
Tests for AutogenOS ActionDispatcher and AutonomousIntentPlanner.
Verifies real-world execution, dynamic subtask decomposition, and causal evidence synthesis.
"""

import pytest
from autogenos.execution.action_dispatcher import ActionDispatcher
from autogenos.swarm.planner import AutonomousIntentPlanner
from autogenos.swarm.graph import SwarmGraphController
from autogenos.core.state import TaskPhase


def test_action_dispatcher_list_windows():
    dispatcher = ActionDispatcher()
    res, evidence = dispatcher.execute_tool("os_list_windows", {})
    assert evidence.passed is True
    assert "windows" in res
    assert isinstance(res["count"], int)


def test_action_dispatcher_shell_execution():
    dispatcher = ActionDispatcher()
    res, evidence = dispatcher.execute_tool("os_exec_shell", {"command": "echo AutogenOS Dispatcher Test"})
    assert evidence.passed is True
    assert res["exit_code"] == 0
    assert "AutogenOS Dispatcher Test" in res["stdout"]


def test_action_dispatcher_file_hash_verification():
    dispatcher = ActionDispatcher()
    res, evidence = dispatcher.execute_tool("verifier_assert_hash", {"file_path": "pyproject.toml"})
    assert evidence.passed is True
    assert res["hash"] is not None
    assert len(res["hash"]) == 64


def test_autonomous_intent_planner_decomposition():
    planner = AutonomousIntentPlanner()
    
    # Composite multi-clause query
    subtasks = planner.plan("Open notepad, then type Hello World, and then capture screen")
    assert len(subtasks) >= 3
    tools = [st.metadata.get("tool") for st in subtasks]
    assert "os_exec_shell" in tools
    assert "os_type_text" in tools
    assert "screen_capture" in tools


@pytest.mark.asyncio
async def test_end_to_end_real_swarm_execution():
    controller = SwarmGraphController()
    state = await controller.run_full_lifecycle("Inspect open windows and verify file hash of pyproject.toml")
    assert state.phase == TaskPhase.COMPLETED
    assert len(state.subtasks) >= 2
    assert len(state.accumulated_evidence) >= 2
    for ev in state.accumulated_evidence:
        assert ev.passed is True
