"""
Tests for SwarmGraphController, Durable State Persistence, and Causal Verification.
"""

import pytest
from autogenos.swarm.graph import SwarmGraphController
from autogenos.swarm.postgres_saver import DurableStateSaver
from autogenos.core.state import SwarmGlobalState, TaskPhase, DeterministicEvidence, EvidenceType


@pytest.mark.asyncio
async def test_durable_checkpointer(tmp_path):
    db_file = tmp_path / "checkpoints.db"
    saver = DurableStateSaver(db_path=db_file)

    state = SwarmGlobalState(master_intent="Automate Excel data processing")
    saver.save_checkpoint(state)

    loaded = saver.load_latest_checkpoint(state.session_id)
    assert loaded is not None
    assert loaded.session_id == state.session_id
    assert loaded.master_intent == state.master_intent


@pytest.mark.asyncio
async def test_swarm_graph_closed_loop_lifecycle():
    controller = SwarmGraphController()
    state = await controller.run_full_lifecycle("Perform atomic cross-stack mutation")
    assert state.phase == TaskPhase.COMPLETED
    assert len(state.subtasks) == 3
    assert len(state.accumulated_evidence) == 3
    assert state.token_usage_pruned > 0


@pytest.mark.asyncio
async def test_verifier_gated_rejection_and_repair():
    controller = SwarmGraphController()
    state = SwarmGlobalState(master_intent="Test failure attribution")
    state = await controller.planner_node(state)
    state = await controller.actor_node(state)

    # Inject failed evidence
    failing_evidence = DeterministicEvidence(
        evidence_type=EvidenceType.SHELL_OUTPUT,
        source_target="sandbox",
        raw_payload="Exit code 1: File not found",
        passed=False
    )
    state = await controller.verifier_node(state, evidence_override=failing_evidence)
    assert state.phase == TaskPhase.REPAIR
    assert len(state.accumulated_evidence) == 0
