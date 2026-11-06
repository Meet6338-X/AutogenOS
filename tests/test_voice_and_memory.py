"""
Integration test for Voice Dynamic EMA Endpointing, CarryOn Compactor, and EchoPath Replay.
"""

from autogenos.voice.turn_detector import DynamicEMAEndpointing, TurnDetectorController
from autogenos.memory.carryon import CarryOnCompactor
from autogenos.memory.echopath import EchoPathReplayEngine, ActionNode


def test_dynamic_ema_endpointing():
    ema = DynamicEMAEndpointing(min_delay=0.5, max_delay=3.0, alpha=0.8, initial_delay=1.0)
    
    # Observe shorter user pauses (e.g. 0.6s)
    updated = ema.update_pause_observation(0.6)
    assert updated < 1.0
    assert updated >= 0.5

    # Check turn completion logic
    assert not ema.should_trigger_turn_end(0.2)
    assert ema.should_trigger_turn_end(2.5)


def test_barge_in_interruption():
    controller = TurnDetectorController()
    controller.set_agent_speaking_state(True)

    # User speaks while agent is speaking
    event = controller.process_vad_chunk(speech_probability=0.9)
    assert event["barge_in"] is True
    assert event["action"] == "flush_audio_queue"
    assert controller.is_agent_speaking is False


def test_carryon_compaction():
    compactor = CarryOnCompactor()
    folded = compactor.fold_subtask(
        task_id="step-101",
        intent="Compile binary and verify symbols",
        intermediate_turn_count=12,
        estimated_raw_tokens=3500,
        final_state={"binary_hash": "e3b0c442"}
    )
    assert folded.tokens_saved > 3000
    assert compactor.total_tokens_pruned > 3000
    summary = compactor.get_compact_prompt_representation()
    assert "step-101" in summary


def test_echopath_replay():
    engine = EchoPathReplayEngine()
    actions = [
        ActionNode(action_type="CLICK", target_relative_coord=(0.4, 0.6)),
        ActionNode(action_type="KEYPRESS", keystroke_payload="Enter")
    ]
    engine.register_successful_trajectory("save_file_dialog", actions)

    found = engine.find_replayable_path("save_file_dialog")
    assert found is not None
    assert len(found.actions) == 2
