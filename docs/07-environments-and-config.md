# 07 — Environments & Configuration Guide

This document describes Lumi's configuration hierarchy, environment variables, and profile defaults for **PC Desktop MVP** versus the future **Raspberry Pi Zero 2 W** target.

---

## 1. Configuration Hierarchy

`main.py` loads configuration at startup in the following precedence (later sources override earlier ones):

1. **Dataclass Defaults** (`AudioConfig`, `SpeechConfig`, `ConversationConfig`, `FaceConfig`, `ControllerConfig`)
2. **`.env` File** (local development convenience via `python-dotenv`, ignored by Git)
3. **OS Environment Variables** (shell exports, systemd service units on Linux/Pi)

> [!IMPORTANT]
> Never commit `.env` or future cloud API keys to Git. Only `.env.example` is tracked in version control.

---

## 2. Configuration Key Reference

| Key | Type | Default | Description |
|---|---|---|---|
| `LUMI_LOG_LEVEL` | `str` | `INFO` | Python logging level (`DEBUG`, `INFO`, `WARNING`, `ERROR`). |
| `LUMI_INTERACTION_MODE` | `str` | `auto_vad` | Listening policy: `auto_vad` (hands-free) or `push_to_talk` (`Space` tap). |
| `LUMI_AUDIO_INPUT_DEVICE` | `str` | `""` | Mic device index or substring (`""` = OS default). |
| `LUMI_AUDIO_OUTPUT_DEVICE` | `str` | `""` | Speaker device index or substring (`""` = OS default). |
| `LUMI_AUDIO_VAD_THRESHOLD` | `float` | `0.015` | Normalized RMS threshold for Auto-VAD speech onset. |
| `LUMI_AUDIO_SILENCE_TIMEOUT` | `float` | `1.2` | Trailing silence (seconds) to end an utterance. |
| `LUMI_AUDIO_SPEECH_START_TIMEOUT` | `float` | `8.0` | Max seconds waiting for speech onset per listen cycle. |
| `LUMI_AUDIO_MAX_UTTERANCE` | `float` | `12.0` | Hard cap (seconds) per captured utterance. |
| `LUMI_VOSK_MODEL_PATH` | `str` | `models/vosk-model-small-fa` | Local directory containing the offline Persian Vosk model. |
| `LUMI_ESPEAK_BIN` | `str` | `espeak-ng` | Executable name or full path to `espeak-ng`. |
| `LUMI_ESPEAK_VOICE` | `str` | `fa` | eSpeak NG voice identifier (`fa` for Persian). |
| `LUMI_ESPEAK_SPEED` | `int` | `160` | Words-per-minute synthesis speed. |
| `LUMI_CONVERSATION_PROVIDER` | `str` | `predefined` | Conversation engine (`predefined` in MVP; `openai` future seam). |
| `LUMI_CONVERSATION_MAX_HISTORY` | `int` | `20` | Rolling RAM context message window size. |
| `LUMI_FACE_WIDTH` | `int` | `480` | Display surface width in pixels. |
| `LUMI_FACE_HEIGHT` | `int` | `320` | Display surface height in pixels. |
| `LUMI_FACE_FPS` | `int` | `60` | Target Pygame animation frame rate. |
| `LUMI_TURN_TIMEOUT_SECONDS` | `float` | `15.0` | Safety timeout for STT/Conversation/TTS steps. |

---

## 3. Desktop PC vs. Future Raspberry Pi Zero 2 W Profiles

Pi Zero 2 W compatibility is **pending hardware benchmarking** (see [FEAT-06](file:///C:/Users/NIAVARAN/Desktop/projects/Lumi/Lumi.Robot/docs/specs/features/06-testing-packaging-and-pi-readiness.md)); the table below outlines expected tuning differences when validating on hardware:

| Setting | PC Desktop MVP | Planned Pi Zero 2 W Validation Profile |
|---|---|---|
| `LUMI_FACE_WIDTH` × `HEIGHT` | `480×320` (windowed) | `320×240` or `240×240` (native SPI/DSI panel) |
| `LUMI_FACE_FPS` | `60` | `20–30` (reduce Cortex-A53 CPU usage) |
| `SDL_VIDEODRIVER` | OS default (`windows` / `x11` / `wayland`) | `kmsdrm` or `fbcon` (headless framebuffer) |
| RAM Target | Unconstrained on PC | `< 280 MB` RSS (within 512 MB board limit) |
