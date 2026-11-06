"""
Comprehensive tests for Autonomous Self-Improvement & Continuous Self-Training Engine:
1. Environmental causal feedback loops (zero hallucination).
2. Trajectory collection & natural DPO/SFT dataset generation.
3. Episodic Memory Reflexion heuristics.
4. Autonomous Tool Induction & composite skill synthesis.
5. REST API telemetry and export endpoints.
"""

import json
import pytest
from pathlib import Path
from starlette.testclient import TestClient

from autogenos.api.server import app
from autogenos.core.state import (
    SwarmGlobalState,
    SubTask,
    ActionProposal,
    DeterministicEvidence,
    EvidenceType,
    TaskPhase
)
from autogenos.self_improvement.self_trainer import (
    TrajectoryCollector,
    PreferenceDatasetGenerator,
    EpisodicMemoryReflector,
    AutonomousToolInducer,
    SelfTrainingEngine,
    ExecutionAttempt,
    TrajectoryRecord
)


@pytest.fixture
def client():
    return TestClient(app)


@pytest.fixture
def sample_swarm_state():
    """Generates a sample SwarmGlobalState with both failed and repaired subtasks."""
    state = SwarmGlobalState(
        master_intent="Inspect system active windows and verify pyproject.toml hash"
    )

    # Subtask 1: Succeeded on first attempt
    subtask_1 = SubTask(
        intent="Inspect system active windows",
        phase=TaskPhase.COMPLETED,
        is_committed=True,
        proposals=[
            ActionProposal(
                actor_id="actor-1",
                description="os_list_windows",
                code_or_payload="os_controller.list_windows()"
            )
        ],
        attached_evidence=[
            DeterministicEvidence(
                evidence_type=EvidenceType.ACCESSIBILITY_TREE,
                source_target="desktop_windows",
                raw_payload="Found 11 active windows",
                passed=True
            )
        ]
    )

    # Subtask 2: Had an initial failed proposal, followed by a repaired proposal
    subtask_2 = SubTask(
        intent="Verify pyproject.toml hash",
        phase=TaskPhase.COMPLETED,
        is_committed=True,
        proposals=[
            ActionProposal(
                actor_id="actor-2",
                description="invalid_sha_check",
                code_or_payload="cat pyproject.toml | bad_hasher"
            ),
            ActionProposal(
                actor_id="actor-2",
                description="verifier_assert_hash",
                code_or_payload="StructAgentVerifier.verify_file_hash('pyproject.toml')"
            )
        ],
        attached_evidence=[
            DeterministicEvidence(
                evidence_type=EvidenceType.FILE_HASH,
                source_target="pyproject.toml",
                raw_payload="SHA-256: 3a7b9c... verified",
                passed=True
            )
        ]
    )

    state.subtasks = [subtask_1, subtask_2]
    state.phase = TaskPhase.COMPLETED
    return state


def test_trajectory_collector_record(tmp_path, sample_swarm_state):
    collector = TrajectoryCollector(storage_dir=str(tmp_path / "trajectories"))
    record = collector.record_swarm_state(sample_swarm_state, duration_sec=1.25)

    assert record.master_intent == sample_swarm_state.master_intent
    assert record.final_phase == TaskPhase.COMPLETED
    assert len(record.subtask_intents) == 2
    assert len(record.chosen_path) >= 1
    assert len(collector.trajectories) == 1

    # Verify JSON file written to disk
    json_files = list(Path(tmp_path / "trajectories").glob("*.json"))
    assert len(json_files) == 1
    data = json.loads(json_files[0].read_text(encoding="utf-8"))
    assert data["master_intent"] == sample_swarm_state.master_intent


def test_preference_dataset_generator_dpo_and_sft():
    # Construct synthetic trajectory with failure and repair
    traj = TrajectoryRecord(
        master_intent="Clone repo and install dependencies",
        final_phase=TaskPhase.COMPLETED,
        subtask_intents=["Clone repo", "Install dependencies"],
        attempts=[
            ExecutionAttempt(
                actor_id="actor-1",
                proposed_tool="git_clone_invalid",
                code_or_payload="git clone http://invalid-url.git",
                evidence_passed=False,
                evidence_payload="Fatal: remote repository not found",
                failure_reason="Exit code 128"
            ),
            ExecutionAttempt(
                actor_id="actor-1",
                proposed_tool="git_clone_valid",
                code_or_payload="git clone https://github.com/Meet6338-X/AutogenOS.git",
                evidence_passed=True,
                evidence_payload="Cloned successfully into AutogenOS",
                failure_reason=None
            )
        ],
        chosen_path=[
            {"intent": "Clone repo", "action": "git clone https://github.com/Meet6338-X/AutogenOS.git", "evidence": "Cloned"}
        ],
        rejected_paths=[
            {"intent": "Clone repo", "action": "git clone http://invalid-url.git", "error": "Fatal: remote repository not found"}
        ]
    )

    # 1. DPO Generation
    dpo_pairs = PreferenceDatasetGenerator.generate_dpo_pairs([traj])
    assert len(dpo_pairs) >= 1
    pair = dpo_pairs[0]
    assert "Clone repo" in pair.prompt
    assert "https://github.com" in pair.chosen
    assert "invalid-url" in pair.rejected
    assert pair.causal_evidence is not None

    # 2. SFT Generation
    sft_samples = PreferenceDatasetGenerator.generate_sft_samples([traj])
    assert len(sft_samples) == 1
    messages = sft_samples[0].messages
    assert len(messages) == 3
    assert messages[0]["role"] == "system"
    assert messages[1]["role"] == "user"
    assert messages[2]["role"] == "assistant"
    assert "verified" in messages[2]["content"].lower()


def test_episodic_memory_reflector(tmp_path):
    rules_file = str(tmp_path / "memory" / "reflection_rules.json")
    reflector = EpisodicMemoryReflector(rules_file=rules_file)

    # Record first failure
    rule1 = reflector.reflect_on_failure(
        domain="os",
        failing_action="click_coordinate(0, 0)",
        error_telemetry="Coordinate (0, 0) belongs to system title bar, action rejected"
    )
    assert rule1.target_domain == "os"
    assert rule1.occurrences == 1
    assert "Avoid 'click_coordinate(0, 0)'" in rule1.recommended_policy

    # Repeat same failure increases occurrence count
    rule2 = reflector.reflect_on_failure(
        domain="os",
        failing_action="click_coordinate(0, 0)",
        error_telemetry="Title bar conflict again"
    )
    assert rule2.occurrences == 2

    # Query relevant heuristics
    matched = reflector.query_relevant_rules("Perform mouse click in os environment")
    assert len(matched) == 1
    assert matched[0].failing_pattern == "click_coordinate(0, 0)"


def test_autonomous_tool_inducer():
    # Construct repeated trajectories
    trajectories = [
        TrajectoryRecord(
            master_intent="Build project A",
            final_phase=TaskPhase.COMPLETED,
            chosen_path=[
                {"action": "pip install -e ."},
                {"action": "pytest tests/ -v"}
            ]
        ),
        TrajectoryRecord(
            master_intent="Build project B",
            final_phase=TaskPhase.COMPLETED,
            chosen_path=[
                {"action": "pip install -e ."},
                {"action": "pytest tests/ -v"}
            ]
        )
    ]

    frequent_seqs = AutonomousToolInducer.identify_frequent_action_sequences(trajectories, min_support=2)
    assert len(frequent_seqs) == 1
    assert frequent_seqs[0] == ["pip install -e .", "pytest tests/ -v"]

    # Synthesize composite tool scaffold
    scaffold = AutonomousToolInducer.synthesize_tool_scaffold(frequent_seqs[0], "install_and_test_pipeline")
    assert scaffold["name"] == "install_and_test_pipeline"
    assert "def install_and_test_pipeline" in scaffold["generated_code"]
    assert "pip install -e ." in scaffold["generated_code"]
    assert "pytest tests/ -v" in scaffold["generated_code"]


def test_self_training_engine_lifecycle(tmp_path, sample_swarm_state):
    engine = SelfTrainingEngine(work_dir=str(tmp_path))
    record = engine.process_completed_run(sample_swarm_state, duration_sec=0.75)
    assert record.final_phase == TaskPhase.COMPLETED

    # Check metrics
    metrics = engine.get_self_training_metrics()
    assert metrics["total_trajectories_recorded"] == 1
    assert metrics["successful_trajectories"] == 1
    assert metrics["success_rate_pct"] == 100.0
    assert metrics["self_training_active"] is True

    # Export datasets
    export_res = engine.export_training_datasets(export_dir=str(tmp_path / "datasets"))
    assert export_res["status"] == "DATASETS_EXPORTED"
    assert Path(export_res["dpo_file"]).exists()
    assert Path(export_res["sft_file"]).exists()


def test_api_self_improvement_endpoints(client):
    # Metrics
    res_m = client.get("/api/v1/self-improvement/metrics")
    assert res_m.status_code == 200
    metrics = res_m.json()
    assert "total_trajectories_recorded" in metrics
    assert "self_training_active" in metrics
    assert metrics["self_training_active"] is True

    # Reflection Rules
    res_r = client.get("/api/v1/self-improvement/rules")
    assert res_r.status_code == 200
    assert "rules" in res_r.json()

    # Tool Induction
    res_i = client.post("/api/v1/self-improvement/induce-tools?min_support=1")
    assert res_i.status_code == 200
    assert "synthesized_tools" in res_i.json()

    # Dataset Export
    res_e = client.post("/api/v1/self-improvement/export-dataset")
    assert res_e.status_code == 200
    assert res_e.json()["status"] == "DATASETS_EXPORTED"
