# Feature 02 — Offline Persian Speech (STT & TTS)

**Feature Identifier:** `FEAT-02`  
**Layer Focus:** `src/lumi/modules/speech/`  
**Shared Contracts Used:** `AudioData`  
**Deliverable:** Offline Persian speech-to-text (`VoskSTTProvider`) and text-to-speech (`EspeakTTSProvider`) behind replaceable provider interfaces  

---

## 1. Overview & Business Value

Lumi must understand spoken Persian and reply verbally **completely offline** after initial model and dependency setup. The `speech` module decouples the rest of the application from specific speech engines: `SpeechToText` converts `AudioData -> str`, and `TextToSpeech` converts `str -> AudioData`.

Because `speech` never touches audio hardware directly, both engines can be benchmarked, mocked, or swapped (e.g., to Piper TTS or Whisper.cpp later) without altering `audio`, `conversation`, or `RobotController`.

---

## 2. Responsibilities & Boundaries

### 2.1 Owns
- `SpeechToText` service/protocol and `VoskSTTProvider` (`vosk_stt_provider.py`).
- `TextToSpeech` service/protocol and `EspeakTTSProvider` (`espeak_tts_provider.py`).
- Engine configuration (`speech_config.py`): model directory, eSpeak binary path, Persian voice id, speech speed/pitch, subprocess timeouts.
- Validation of incoming `AudioData` format before recognition and normalization of WAV bytes into `AudioData` after synthesis.

### 2.2 Does NOT Own
- Microphone recording or speaker output (`AudioService` owns playback/capture).
- Text normalization for intent matching (`Conversation` owns NLP normalization).
- Cloud API calls (strictly prohibited in MVP).

---

## 3. Interfaces & Contracts

```python
from typing import Protocol
from lumi.shared.models import AudioData

class SpeechToTextProvider(Protocol):
    def transcribe(self, audio: AudioData) -> str:
        """Transcribe spoken Persian audio into text. Returns '' when nothing is recognized."""
        ...

class TextToSpeechProvider(Protocol):
    def synthesize(self, text: str) -> AudioData:
        """Synthesize Persian text into PCM AudioData. Raises SpeechSynthesisError on failure."""
        ...
```

Thin service wrappers (`SpeechToText` in `speech_to_text.py`, `TextToSpeech` in `text_to_speech.py`) validate inputs, enforce non-empty/format checks, delegate to the injected provider, and map provider errors into local exceptions (`SpeechModelLoadError`, `SpeechRecognitionError`, `SpeechSynthesisError`).

---

## 4. Provider Specifications

### 4.1 `VoskSTTProvider` (Offline Persian STT)
- **Engine:** `vosk` Python bindings (`Model`, `KaldiRecognizer`), `SetLogLevel(-1)` by default to keep console logs clean.
- **Expected Model:** Small offline Persian Vosk model (e.g., `vosk-model-small-fa-0.4` or equivalent `vosk-model-small-fa-*`), stored externally at `SpeechConfig.vosk_model_path` (default `models/vosk-model-small-fa`) and acquired via documented setup instructions (not committed to Git or bundled in wheel).
- **Input Format Validation:** Requires `sample_rate == 16000`, `channels == 1`, `sample_width == 2`. Rejects mismatched `AudioData` with an explicit `ValueError`/`SpeechRecognitionError`.
- **Execution:** Feeds `audio.samples` to `KaldiRecognizer(model, audio.sample_rate)`, calls `FinalResult()`, parses JSON `"text"` field, strips whitespace, and returns `""` if empty.
- **Startup Check:** Loads `Model(model_path)` once at initialization (not per utterance) and fails fast with a clear error message + model download hint if the directory is missing.

### 4.2 `EspeakTTSProvider` (Offline Persian TTS)
- **Engine:** `espeak-ng` CLI binary invoked via `subprocess.run` (cross-platform on Windows and Raspberry Pi Linux without CFFI/shared-library headaches).
- **Command:** `espeak-ng -v fa -s <rate> -p <pitch> --stdout "<text>"` (or writing via stdin to avoid shell/argument length issues and escaping edge cases). Using `input=text.encode("utf-8")` with `--stdin` or safe argument list (`shell=False`) avoids command injection.
- **WAV Parsing:** Reads the stdout WAV stream using Python stdlib `wave` (`io.BytesIO`), extracts `nchannels`, `sampwidth`, `framerate`, and raw PCM frames, and returns `AudioData(samples=frames, sample_rate=framerate, channels=nchannels, sample_width=sampwidth)`.
- **Validation & Timeouts:**
  - Rejects empty/whitespace-only text without spawning a subprocess.
  - Enforces `tts_timeout_seconds` (default `10.0s`) on `subprocess.run`.
  - Checks `shutil.which(espeak_binary)` during initialization so missing OS installation fails fast with clear setup instructions.

---

## 5. Risks, Dependencies & Validation Gates

- **System Dependency — `espeak-ng`:** Must be installed on the host OS (Windows installer/PATH or `apt install espeak-ng` on Debian/Raspberry Pi OS). Robotic voice quality is explicitly accepted for MVP.
- **External Model Acquisition — Vosk Persian Model:** License (typically Apache 2.0 for official Vosk models) and download URL/checksum must be verified and documented in setup docs during `FEAT-06`.
- **Persian Quality Risk:** Small offline Vosk models can misrecognize colloquial Tehrani Persian or noisy audio; `Conversation`'s `PredefinedIntentMatcher` must tolerate minor recognition variations (covered in `FEAT-03`).

---

## 6. Acceptance Criteria

1. `VoskSTTProvider` fails fast at startup with an actionable error when `vosk_model_path` does not exist.
2. `SpeechToText.transcribe(audio)` rejects non-16kHz/non-mono/non-int16 `AudioData` cleanly and returns stripped string output (including `""` on silence) using a fake recognizer in unit tests.
3. `EspeakTTSProvider` fails fast if `espeak-ng` is missing, converts stdout WAV bytes into valid `AudioData` without playing sound to speakers, and enforces timeout limits.
4. Neither `speech_to_text.py` nor `text_to_speech.py` imports `sounddevice`, `pygame`, or `conversation`.
5. No raw audio recordings are written to disk or logged at `INFO` level.
