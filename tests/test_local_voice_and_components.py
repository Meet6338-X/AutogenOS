"""
Tests for local 100% free offline voice components and open-source tool integrations.
"""

from pathlib import Path
from autogenos.components.local_tts import LocalTTS
from autogenos.components.local_whisper import LocalWhisperSTT
from autogenos.components.livekit_local import LocalLiveKitServer
from autogenos.components.screen_vision import ScreenVisionEngine
from autogenos.components.vector_search import LocalVectorStore
from autogenos.components.terminal_runner import TerminalRunner


def test_local_tts_synthesis(tmp_path):
    tts = LocalTTS()
    wav_out = tmp_path / "test_tone.wav"
    out = tts.synthesize_wav_file("Testing local voice synthesis.", wav_out)
    assert out.exists()
    assert out.stat().st_size > 44  # Valid WAV header + PCM samples


def test_local_livekit_server():
    server = LocalLiveKitServer(port=7880)
    success, msg = server.start_local_livekit()
    assert success is True
    info = server.get_connection_info()
    assert "ws://127.0.0.1:7880" in info["url"]
    assert info["mode"] == "100% LOCAL FREE"
    server.stop_server()


def test_screen_vision_engine(tmp_path):
    engine = ScreenVisionEngine(snapshots_dir=tmp_path)
    img = engine.capture_fullscreen()
    assert img.width > 0
    assert img.height > 0

    dhash = engine.compute_dhash(img)
    assert len(dhash) > 0

    saved_path = engine.save_screenshot("test_screen.png")
    assert saved_path.exists()


def test_local_vector_store():
    store = LocalVectorStore()
    store.add_document("doc1", "Automate windows applications and inject keystrokes", {"tag": "os"})
    store.add_document("doc2", "Navigate browser pages and evaluate JavaScript via CDP", {"tag": "web"})
    store.add_document("doc3", "Calculate SHA256 file hashes for causal verification", {"tag": "verifier"})
    store.build_index()

    matches = store.search("keystrokes and mouse click", top_k=1)
    assert len(matches) > 0
    assert matches[0][0]["id"] == "doc1"


def test_terminal_runner():
    runner = TerminalRunner()
    result = runner.execute("python --version")
    assert result["exit_code"] == 0
    assert "Python" in result["stdout"] or "Python" in result["stderr"]
    assert result["success"] is True
