# 03 — Audio I/O & Offline Persian Speech Guide

This document explains how Lumi captures spoken Persian audio, detects utterances, transcribes speech offline with Vosk, synthesizes Persian responses offline with eSpeak NG, and plays audio back safely.

---

## 1. End-to-End Voice Signal Pipeline

```text
[Microphone]
    │  16kHz / Mono / int16 PCM (30ms blocks)
    ▼
[AudioService.record_utterance()]  ──(speech onset)──> on_speech_onset() -> Face: LISTENING
    │  Returns AudioData (or None on timeout/cancel)
    ▼
[SpeechToText (VoskSTTProvider)]
    │  Returns normalized Persian string (or "" if unrecognized)
    ▼
[ConversationService.respond()] -> (reply_text, Emotion)
    │
    ▼
[TextToSpeech (EspeakTTSProvider)]
    │  Synthesizes WAV via `espeak-ng` -> parses into AudioData
    ▼
[AudioService.play_audio()]        ──(half-duplex: mic capture paused; Space cancels <150ms)
    │
    ▼
[Speakers]
```

---

## 2. Audio I/O & Utterance Detection (`modules/audio/`)

### 2.1 Standard Format
All capture defaults to **16,000 Hz, Mono (1 channel), signed 16-bit PCM (`sample_width=2`)**, matching Vosk's native input expectations with zero resampling overhead.

### 2.2 Auto-VAD vs. Manual `Space` Trigger
- **Auto-VAD (Default, `LUMI_INTERACTION_MODE=auto_vad`):**
  1. Streams audio blocks (`30 ms`) while Lumi remains visually `IDLE`.
  2. When RMS energy exceeds `vad_rms_threshold` for 2 consecutive blocks, invokes `on_speech_onset()` (switching Face to `LISTENING`) and prepends `0.3s` of `pre_roll_seconds` ring buffer so the opening syllable isn't clipped.
  3. Stops when trailing silence reaches `silence_timeout_seconds` (`1.2s`), `max_utterance_seconds` (`12.0s`) is hit, or the user taps `Space` (`stop_event`) to submit immediately.
  4. Discards sub-`0.25s` noise bursts (`return None`).
- **Push-to-Talk (`LUMI_INTERACTION_MODE=push_to_talk`):**
  - Waits in `IDLE` until the user taps `Space`, records immediately (`wait_for_speech=False`), and finishes on trailing silence or a second `Space` tap.

### 2.3 Half-Duplex Playback & Barge-In
- `play_audio()` writes PCM chunks (~50ms) to `sounddevice.OutputStream`, checking `cancel_event` between chunks so `Space` barge-in or shutdown stops audio within `<=150ms`.
- Because capture only runs in `LISTENING`, Lumi will not hear its own speaker output during `SPEAKING`.

---

## 3. Offline Speech-to-Text (`VoskSTTProvider`)

- **Model Loading:** Loads `vosk.Model(str(vosk_model_path))` once at startup. Fails fast with a clear `SpeechModelLoadError` if the folder is missing.
- **Format Guard:** Explicitly validates `sample_rate == 16000`, `channels == 1`, `sample_width == 2` before invoking `KaldiRecognizer`.
- **Output:** Parses Vosk JSON `FinalResult()` (`"text"` field), strips whitespace, and returns `""` when nothing was recognized.

---

## 4. Offline Text-to-Speech (`EspeakTTSProvider`)

- **Why Subprocess CLI:** Invoking `espeak-ng -v fa -s <rate> -p <pitch> --stdin --stdout` via `subprocess.run(..., shell=False, timeout=...)` avoids native C-library binding fragility across Windows and Raspberry Pi Linux while preventing shell-injection issues.
- **WAV Normalization:** Parses stdout bytes with Python stdlib `wave` + `io.BytesIO`, returning `AudioData` to `RobotController`. `TextToSpeech` never writes directly to speakers.
- **Voice Quality Expectation:** eSpeak NG produces an intelligible, robotic Persian voice suitable for the offline MVP; `TextToSpeechProtocol` isolates it so higher-fidelity offline engines (e.g., Piper TTS) can replace it later in one provider file.
