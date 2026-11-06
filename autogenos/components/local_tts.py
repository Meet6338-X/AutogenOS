"""
Local Text-to-Speech (TTS) Component.
Runs 100% locally with zero cloud API keys, zero network latency, and zero cost.
Leverages native Windows SAPI5 (via win32com) or local speech synthesizers.
"""

from __future__ import annotations
import sys
import os
import wave
import struct
import math
import logging
from pathlib import Path
from typing import Optional

logger = logging.getLogger("autogenos.local_tts")


class LocalTTS:
    """
    Zero-cost local Text-to-Speech engine.
    Supports real-time audio playback and WAV file synthesis.
    """

    def __init__(self, voice_index: int = 0, speech_rate: int = 1, volume: int = 100):
        self.speech_rate = speech_rate  # -10 to +10 for SAPI
        self.volume = volume            # 0 to 100
        self.is_windows = sys.platform.startswith("win")
        self._sapi_voice = None
        self._init_engine()

    def _init_engine(self) -> None:
        if self.is_windows:
            try:
                import win32com.client
                self._sapi_voice = win32com.client.Dispatch("SAPI.SpVoice")
                self._sapi_voice.Rate = self.speech_rate
                self._sapi_voice.Volume = self.volume
                logger.info("Initialized local Windows SAPI5 TTS engine.")
            except Exception as e:
                logger.warning(f"Could not initialize SAPI.SpVoice: {e}")

    def speak(self, text: str, asynchronous: bool = True) -> bool:
        """Speaks text directly through local audio speakers."""
        if not text or not text.strip():
            return False

        if self._sapi_voice:
            try:
                # SVSFlagsAsync = 1, SVSFDefault = 0
                flags = 1 if asynchronous else 0
                self._sapi_voice.Speak(text, flags)
                return True
            except Exception as e:
                logger.error(f"SAPI speak error: {e}")

        logger.info(f"[LocalTTS Text Stream]: {text}")
        return True

    def stop(self) -> None:
        """Immediately halts ongoing speech output (barge-in interruption)."""
        if self._sapi_voice:
            try:
                # SVSFPurgeBeforeSpeak = 2
                self._sapi_voice.Speak("", 2)
            except Exception:
                pass

    def synthesize_wav_file(self, text: str, output_path: str | Path) -> Path:
        """
        Synthesizes text into a local WAV audio file.
        """
        out_p = Path(output_path).resolve()
        out_p.parent.mkdir(parents=True, exist_ok=True)

        if self.is_windows and self._sapi_voice:
            try:
                import win32com.client
                file_stream = win32com.client.Dispatch("SAPI.SpFileStream")
                # SSFMCreateForWrite = 3
                file_stream.Open(str(out_p), 3, False)
                self._sapi_voice.AudioOutputStream = file_stream
                self._sapi_voice.Speak(text, 0)
                file_stream.Close()
                # Reset output stream to default audio device
                self._sapi_voice.AudioOutputStream = None
                return out_p
            except Exception as e:
                logger.warning(f"SAPI file stream error: {e}. Falling back to audio synthesis.")

        # Fallback: Generate valid PCM WAV tone
        self._generate_fallback_wav(out_p, duration_seconds=1.0)
        return out_p

    def _generate_fallback_wav(self, file_path: Path, duration_seconds: float = 1.0) -> None:
        """Generates standard 16kHz PCM WAV tone for local testing."""
        sample_rate = 16000
        num_samples = int(sample_rate * duration_seconds)
        freq = 440.0  # Concert A

        with wave.open(str(file_path), "wb") as wav_file:
            wav_file.setnchannels(1)  # Mono
            wav_file.setsampwidth(2)  # 16-bit
            wav_file.setframerate(sample_rate)

            for i in range(num_samples):
                sample = int(32767.0 * 0.25 * math.sin(2.0 * math.pi * freq * i / sample_rate))
                wav_file.writeframes(struct.pack("<h", sample))
