# Feature 01 — Audio I/O & Voice Activity Detection

**Feature Identifier:** `FEAT-01`  
**Layer Focus:** `src/lumi/modules/audio/`  
**Shared Contracts Used:** `AudioData`  
**Deliverable:** Offline microphone capture (with Auto-VAD and manual trigger/cancel) and speaker playback via `sounddevice`  

---

## 1. Overview & Business Value

Lumi's voice pipeline starts and ends with physical sound hardware. The `audio` module abstracts `sounddevice` (PortAudio) behind a small, testable service interface so Lumi can capture spoken Persian utterances and play synthesized responses on PC speakers—while allowing unit and controller tests to run completely without microphones or speakers.

---

## 2. Responsibilities & Boundaries

### 2.1 Owns
- Microphone and speaker device discovery/validation (`audio_devices.py`).
- Audio capture configuration: sample rate, channels, dtype, chunk duration, VAD thresholds, and timeouts (`audio_config.py`).
- Utterance recording with energy-based Voice Activity Detection (Auto-VAD) and manual/timeout boundaries (`audio_service.py`).
- Synchronous/cancellable playback of `AudioData` to the selected output device.

### 2.2 Does NOT Own
- Speech recognition or transcription (never imports `speech` or returns text).
- Text-to-speech synthesis.
- Conversation turn orchestration or deciding *when* to listen (`RobotController` decides).

---

## 3. Interfaces & Contracts

```python
from collections.abc import Callable
from typing import Protocol
import threading
from lumi.shared.models import AudioData

class AudioServiceProtocol(Protocol):
    def record_utterance(
        self,
        cancel_event: threading.Event | None = None,
        stop_event: threading.Event | None = None,
        wait_for_speech: bool = True,
        on_speech_onset: Callable[[], None] | None = None,
    ) -> AudioData | None:
        """Capture one spoken utterance and return AudioData.

        - cancel_event: hard abort (e.g., shutdown); discards buffered audio and returns None.
        - stop_event: graceful manual finalize (e.g., Space tap while listening); returns captured audio if >= min duration, else None.
        - on_speech_onset: invoked once when VAD detects speech onset so the controller can switch Face from IDLE to LISTENING.
        """
        ...

    def play_audio(
        self,
        audio: AudioData,
        cancel_event: threading.Event | None = None,
    ) -> bool:
        """Play AudioData to speaker. Returns True if completed, False if cancelled."""
        ...

    def close(self) -> None:
        """Release any held audio resources."""
        ...
```

### 3.1 Configuration (`AudioConfig`)
| Field | Default | Description |
|---|---|---|
| `sample_rate` | `16000` | Capture sample rate (Hz); matches Vosk input format. |
| `channels` | `1` | Mono capture. |
| `sample_width` | `2` | `int16` PCM (2 bytes/sample). |
| `block_duration_ms` | `30` | Chunk size per callback/read (`480` frames at 16kHz). |
| `vad_rms_threshold` | `0.015` | Normalized float RMS (`0.0..1.0`) or `int16` equivalent (`~500`) above ambient floor. |
| `silence_timeout_seconds` | `1.2` | Trailing silence duration that closes an active utterance. |
| `speech_start_timeout_seconds` | `8.0` | Max wait for voice onset before returning `None` in Auto-VAD wait. |
| `max_utterance_seconds` | `12.0` | Hard cap on a single recorded utterance. |
| `pre_roll_seconds` | `0.3` | Ring buffer prepended when speech onset triggers so first syllable isn't clipped. |
| `input_device` | `None` | Device index or substring name (`None` = OS default). |
| `output_device` | `None` | Device index or substring name (`None` = OS default). |

---

## 4. Capture & Playback Behavior

### 4.1 Utterance Detection (Auto-VAD + Manual Tap Mode)
```text
[Wait for onset] ──(RMS > threshold for 2 consecutive blocks)──> invoke on_speech_onset() ──> [Recording]
       │                                                                                          │
       ├─(speech_start_timeout elapsed)──> return None                                            ├─(silence >= silence_timeout)──> trim tail, return AudioData
       ├─(stop_event set)────────────────> return None                                            ├─(stop_event set)──────────────> finalize & return AudioData (if >=0.25s)
       └─(cancel_event set)──────────────> return None (discard)                                  ├─(max_utterance elapsed)──────> return AudioData
                                                                                                  └─(cancel_event set)───────────> return None (discard)
```
- **Auto-VAD mode (`wait_for_speech=True`):** Waits passively in `IDLE` up to `speech_start_timeout_seconds` for speech onset, fires `on_speech_onset()` when voice begins, prepends `pre_roll_seconds`, and records until `silence_timeout_seconds` of trailing silence, `stop_event`, or `max_utterance_seconds`.
- **Manual Tap-to-Trigger (`wait_for_speech=False`, Space tap in `push_to_talk` or after barge-in):** Begins recording immediately until `silence_timeout_seconds` of trailing silence, a second `Space` tap (`stop_event` to finalize immediately), or `max_utterance_seconds`.
- **Hard Abort vs. Graceful Finalize:** `cancel_event` (used on shutdown or playback barge-in) aborts immediately and returns `None`; `stop_event` finalizes any valid captured speech (`>=0.25s`) and returns `AudioData`.
- **Short Noise Rejection:** Utterances shorter than `0.25s` of voiced audio are discarded (`return None`) to avoid clicks/pops triggering STT.

### 4.2 Speaker Playback & Cancellation
- Plays `audio.samples` using `audio.sample_rate`, `audio.channels`, and `audio.sample_width` via `sounddevice.OutputStream` in small chunks (e.g., 50ms) rather than one uninterruptible `sd.wait()`.
- Chunked playback checks `cancel_event.is_set()` between writes so pressing `Space` (barge-in) or closing the app stops playback within `<100ms`.
- Half-duplex protection: `AudioService` does not keep an active mic stream feeding STT during `play_audio`.

### 4.3 Device Resolution & Error Handling (`audio_devices.py`)
- Supports device lookup by integer index, exact/partial case-insensitive device name, or OS default.
- Raises explicit domain exceptions (`AudioDeviceNotFoundError`, `AudioStreamError`) rather than leaking raw `sounddevice.PortAudioError` types across module boundaries.
- Never logs raw PCM payloads.

---

## 5. Risks & Mitigations

- **Risk — Ambient Room Noise False Triggers:** Fixed RMS threshold may trigger on fan noise or fail on quiet mics. *Mitigation:* Configurable `vad_rms_threshold`, short-burst rejection (`<0.25s`), and Spacebar manual override; optional future enhancement is 1-second startup ambient calibration without complicating MVP.
- **Risk — Sample Rate Mismatch on USB Mics / Pi Soundcards:** Some hardware rejects 16kHz directly. *Mitigation:* Document `16000 Hz` requirement and validate stream open at startup; if hardware requires `44100/48000 Hz` later, local decimation stays inside `audio`.

---

## 6. Acceptance Criteria

1. With a fake input stream, `record_utterance()` fires `on_speech_onset()`, prepends pre-roll frames, captures voiced blocks, stops after `silence_timeout_seconds` of silence, and returns valid `AudioData(16000, 1, 2)`.
2. Pure silence or sub-250ms noise bursts return `None` without hanging past `speech_start_timeout_seconds`.
3. Setting `cancel_event` aborts `record_utterance()` (returning `None`) and interrupts `play_audio()` within `<=150ms`; setting `stop_event` finalizes valid captured speech cleanly.
4. `play_audio()` respects the `sample_rate` and `channels` provided on the incoming `AudioData`.
5. Missing or invalid input/output device configuration raises a clean `AudioDeviceNotFoundError` with actionable diagnostics.
