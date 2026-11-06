"""
Tests for RSIAgent Exploration, UI-Evol Critique, and OSWorld/Agent-Diff evaluation harnesses.
"""

import pytest
from autogenos.self_improvement.rsi_agent import RSIAgentEngine
from autogenos.memory.ui_evol import UIEvolEngine, GUIStateObservation
from autogenos.eval.agent_diff import AgentDiffEvaluator, StateSnapshot
from autogenos.eval.osworld_runner import OSWorldEvaluationRunner


@pytest.mark.asyncio
async def test_rsi_agent_broad_and_deep_exploration():
    rsi = RSIAgentEngine()
    results = await rsi.run_exploration_cycle(["Calculator", "Terminal"])
    assert results["broad_tasks_explored"] == 2
    assert results["frozen_memories_compiled"] >= 2


def test_ui_evol_retrace_and_critique():
    engine = UIEvolEngine()
    planned = [{"target": "save_button_ax_1"}]
    telemetry = [
        GUIStateObservation(
            step_index=0,
            expected_element_id="save_button_ax_1",
            observed_dom_tree_hash="shifted_hash_v2",
            error_message="Element save_button_ax_1 not visible"
        )
    ]

    divergences = engine.retrace_divergence(planned, telemetry)
    assert len(divergences) == 1

    matrix = engine.critique_and_evolve("AppX", divergences, {})
    assert matrix.repaired_steps_count == 1
    assert "save_button_ax_1" in matrix.evolved_locators


def test_agent_diff_evaluation():
    evaluator = AgentDiffEvaluator()
    base = StateSnapshot(snapshot_id="base", file_hashes={"main.py": "hash_a"})
    current = StateSnapshot(snapshot_id="current", file_hashes={"main.py": "hash_b", "output.txt": "hash_c"})

    report = evaluator.evaluate_diff(
        baseline=base,
        current=current,
        expected_modifications={"main.py"},
        expected_additions={"output.txt"}
    )
    assert report.passed is True
    assert report.score == 1.0
    assert len(report.unexpected_side_effects) == 0


def test_osworld_runner():
    runner = OSWorldEvaluationRunner(task_id="osworld-test")
    runner.evaluate_step(
        step_num=1,
        action_type="CLICK",
        target_app="Calc",
        expected_state_predicate=True,
        implicit_condition_met=True
    )
    report = runner.finalize_task()
    assert report.success is True
    assert report.implicit_state_accuracy == 100.0
