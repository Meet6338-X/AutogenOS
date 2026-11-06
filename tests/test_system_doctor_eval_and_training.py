"""
Test Suite for AutogenOS System Doctor, Benchmark Evaluation Harness, and LoRA Fine-Tuning Engine.
"""

import os
import json
import pytest
from pathlib import Path
from starlette.testclient import TestClient

from autogenos.core.system_doctor import SystemDoctor, SystemDoctorReport
from autogenos.eval.benchmark_harness import BenchmarkHarness, MasterBenchmarkReport
from autogenos.self_improvement.self_trainer import (
    LoRATrainer,
    LoRATrainingConfig,
    LoRATrainingRunResult,
    SelfTrainingEngine,
)
from autogenos.api.server import app


@pytest.fixture
def client():
    return TestClient(app)


def test_system_doctor_diagnostics(tmp_path):
    doctor = SystemDoctor(work_dir=str(tmp_path))
    report = doctor.run_diagnostics()

    assert isinstance(report, SystemDoctorReport)
    assert report.total_checks >= 6
    assert report.passed_checks >= 5
    assert report.overall_health in ["HEALTHY (10/10)", "FUNCTIONAL (9/10)"]

    cli_out = doctor.format_cli_output(report)
    assert "AUTOGENOS SYSTEM DOCTOR DIAGNOSTIC REPORT" in cli_out
    assert "Overall Health" in cli_out


def test_benchmark_harness_suites(tmp_path):
    harness = BenchmarkHarness(temp_work_dir=str(tmp_path))

    # Test individual suites
    osworld_res = harness.run_suite("osworld")
    assert osworld_res.passed is True
    assert osworld_res.score_pct == 100.0

    diff_res = harness.run_suite("agent-diff")
    assert diff_res.passed is True
    assert diff_res.score_pct == 100.0

    tool_res = harness.run_suite("tool-attention")
    assert tool_res.score_pct > 70.0

    # Test master run
    master = harness.run_all()
    assert isinstance(master, MasterBenchmarkReport)
    assert master.total_suites == 3
    assert master.passed_suites == 3
    assert master.overall_score_pct > 80.0

    report_str = harness.format_cli_report(master)
    assert "AUTOGENOS EMPIRICAL BENCHMARK EVALUATION REPORT" in report_str


def test_lora_trainer_and_recipe_generation(tmp_path):
    trainer = LoRATrainer()
    config = LoRATrainingConfig(
        base_model="meta-llama/Llama-3.2-3B-Instruct",
        epochs=3,
        mode="DPO",
        output_adapter_dir=str(tmp_path / "adapters")
    )

    unsloth_recipe = trainer.generate_unsloth_recipe(config, "dummy_ds.jsonl")
    assert "FastLanguageModel.from_pretrained" in unsloth_recipe
    assert "DPOTrainer" in unsloth_recipe

    hf_recipe = trainer.generate_huggingface_recipe(config, "dummy_ds.jsonl")
    assert "get_peft_model" in hf_recipe

    result = trainer.execute_training(config, samples_count=5)
    assert isinstance(result, LoRATrainingRunResult)
    assert result.status == "COMPLETED"
    assert result.final_loss < result.initial_loss
    assert len(result.loss_history) == 3

    adapter_cfg = Path(result.output_adapter_dir) / "adapter_config.json"
    assert adapter_cfg.exists()
    data = json.loads(adapter_cfg.read_text(encoding="utf-8"))
    assert data["base_model_name_or_path"] == "meta-llama/Llama-3.2-3B-Instruct"


def test_self_training_engine_local_adapter_integration(tmp_path):
    engine = SelfTrainingEngine(work_dir=str(tmp_path))
    res = engine.train_local_adapter(
        config=LoRATrainingConfig(epochs=2, output_adapter_dir=str(tmp_path / "adapter_test"))
    )

    assert res.status == "COMPLETED"
    assert len(engine.training_runs) == 1
    assert Path(res.output_adapter_dir).exists()


def test_api_system_doctor_and_eval_endpoints(client):
    # Test System Doctor
    doc_resp = client.get("/api/v1/system/doctor")
    assert doc_resp.status_code == 200
    doc_data = doc_resp.json()
    assert "overall_health" in doc_data
    assert "checks" in doc_data

    # Test Benchmarks GET
    bench_resp = client.get("/api/v1/eval/benchmarks")
    assert bench_resp.status_code == 200
    bench_data = bench_resp.json()
    assert bench_data["passed_suites"] == 3

    # Test Eval Run POST
    run_resp = client.post("/api/v1/eval/run", json={"suite": "osworld"})
    assert run_resp.status_code == 200
    assert run_resp.json()["passed"] is True


def test_api_lora_training_endpoints(client, tmp_path):
    train_resp = client.post(
        "/api/v1/self-improvement/train",
        json={
            "base_model": "meta-llama/Llama-3.2-3B-Instruct",
            "mode": "DPO",
            "epochs": 2,
            "output_adapter_dir": str(tmp_path / "api_adapter")
        }
    )
    assert train_resp.status_code == 200
    train_data = train_resp.json()
    assert train_data["status"] == "COMPLETED"
    assert train_data["final_loss"] < train_data["initial_loss"]

    # Check training-runs list
    runs_resp = client.get("/api/v1/self-improvement/training-runs")
    assert runs_resp.status_code == 200
    runs_data = runs_resp.json()
    assert runs_data["count"] >= 1
