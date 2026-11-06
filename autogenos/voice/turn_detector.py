"""
Continuous Voice Pipeline: Turn Detection and Dynamic EMA Endpointing.
Maintains sub-500ms conversational Time-to-First-Audio (TTFA) with dynamic user cadence adaptation.
"""

from __future__ import annotations
import time
import logging
from typing import Optional

logger = logging.getLogger("autogenos.voice")


class DynamicEMAEndpointing:
    """
    Dynamically adapts end-of-turn silence threshold using Exponential Moving Average (EMA).
    D_t = alpha * D_{t-1} + (1 - alpha) * P_observed
    Clamped to [min_delay, max_delay].
    """

    def __init__(
        self,
        min_delay: float = 0.5,
        max_delay: float = 3.0,
        alpha: float = 0.9,
        initial_delay: float = 0.8
    ):
        self.min_delay = min_delay
        self.max_delay = max_delay
        self.alpha = alpha
        self.current_delay = initial_delay

    def update_pause_observation(self, observed_pause_seconds: float) -> float:
        """Updates moving average with the latest user pause sample."""
        self.current_delay = (self.alpha * self.current_delay) + ((1.0 - self.alpha) * observed_pause_seconds)
        self.current_delay = max(self.min_delay, min(self.max_delay, self.current_delay))
        return self.current_delay

    def should_trigger_turn_end(self, silence_duration_seconds: float) -> bool:
        """Determines if the silence duration warrants dispatching an end-of-turn event."""
        return silence_duration_seconds >= self.current_delay


class TurnDetectorController:
    """
    Coordinates 32ms audio frames from Silero VAD and 160ms TurnDetector v1-mini predictions.
    Handles barge-in interruption events to halt pending TTS audio playback.
    """

    def __init__(self, ema: Optional[DynamicEMAEndpointing] = None):
        self.ema = ema or DynamicEMAEndpointing()
        self.is_user_speaking: bool = False
        self.is_agent_speaking: bool = False
        self.last_speech_time: float = 0.0
        self.silence_start_time: Optional[float] = None

    def process_vad_chunk(self, speech_probability: float, threshold: float = 0.5) -> dict:
        """
        Processes 32ms audio frame (e.g. 512 samples at 16kHz from Silero VAD).
        Detects immediate barge-in interruption or transition into silence.
        """
        now = time.time()
        event = {"action": "continue", "barge_in": False, "turn_complete": False}

        if speech_probability >= threshold:
            if not self.is_user_speaking:
                self.is_user_speaking = True
                self.silence_start_time = None
                # Check for barge-in: user spoke while agent was outputting audio
                if self.is_agent_speaking:
                    logger.info("Barge-in interruption detected! Truncating agent TTS stream.")
                    event["barge_in"] = True
                    event["action"] = "flush_audio_queue"
                    self.is_agent_speaking = False
            self.last_speech_time = now
        else:
            if self.is_user_speaking:
                # User just stopped speaking, start silence timer
                if self.silence_start_time is None:
                    self.silence_start_time = now
                
                silence_duration = now - self.silence_start_time
                if self.ema.should_trigger_turn_end(silence_duration):
                    self.is_user_speaking = False
                    self.ema.update_pause_observation(silence_duration)
                    event["turn_complete"] = True
                    event["action"] = "dispatch_llm_turn"
                    self.silence_start_time = None
                    logger.info(f"Turn complete detected. Adapted endpointing delay: {self.ema.current_delay:.2f}s")

        return event

    def set_agent_speaking_state(self, speaking: bool) -> None:
        self.is_agent_speaking = speaking
