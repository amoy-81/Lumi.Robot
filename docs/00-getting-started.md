# 00 — Getting Started Guide

**Project:** Lumi (`lumi-robot`, Offline Persian Desktop Companion)  
**Platform:** Python `3.11+` (`src/lumi` package layout)  
**Audio / Speech:** `sounddevice` (PortAudio), `vosk` (offline Persian STT), `espeak-ng` (offline Persian TTS)  
**Face Renderer:** `pygame` (asset-free geometric eyes)  
**Architecture:** Four isolated modules (`audio`, `speech`, `conversation`, `face`) coordinated by `RobotController`  

---

## 1. Prerequisites

Before running Lumi locally on a PC (Windows or Linux), ensure you have:
- **Python 3.11+**: Verify with `python --version`.
- **eSpeak NG (`espeak-ng`)**: System binary for offline Persian text-to-speech.
  - **Windows:** Install from the official `espeak-ng` release installer and ensure `espeak-ng.exe` is on `PATH`.
  - **Linux (Ubuntu/Debian/Raspberry Pi OS):** `sudo apt install espeak-ng portaudio19-dev`.
  - Verify with `espeak-ng -v fa --version` (or `espeak-ng -v fa "سلام" --stdout > test.wav`).
- **Offline Persian Vosk Model**: Download the small Persian model (e.g., `vosk-model-small-fa-0.4` / `vosk-model-small-fa-*` from AlphaCephei Vosk models) and extract it so `models/vosk-model-small-fa/` contains `am/`, `conf/`, `graph/`, etc.
- **Working Microphone & Speakers**: Built-in or USB audio I/O recognized by your OS.

---

## 2. Virtual Environment & Package Installation

Create a virtual environment and install Lumi in editable mode with dev tools:

```bash
python -m venv .venv
# Windows (PowerShell / cmd):
.venv\Scripts\activate
# Linux / macOS:
source .venv/bin/activate

pip install -e .[dev]
```

> [!NOTE]
> Once dependencies and the Vosk model are installed, Lumi runs **100% offline**. No cloud API keys or internet access are required for MVP.

---

## 3. Configuration Setup

Copy `.env.example` to `.env` in the repository root and adjust paths or audio devices if needed:

```env
LUMI_LOG_LEVEL=INFO
LUMI_INTERACTION_MODE=auto_vad
LUMI_VOSK_MODEL_PATH=models/vosk-model-small-fa
LUMI_ESPEAK_BIN=espeak-ng
LUMI_ESPEAK_VOICE=fa
LUMI_AUDIO_INPUT_DEVICE=
LUMI_AUDIO_OUTPUT_DEVICE=
LUMI_FACE_WIDTH=480
LUMI_FACE_HEIGHT=320
LUMI_FACE_FPS=60
LUMI_CONVERSATION_PROVIDER=predefined
```

Leave `LUMI_AUDIO_INPUT_DEVICE` and `LUMI_AUDIO_OUTPUT_DEVICE` empty to use the operating system's default microphone and speakers.

---

## 4. Running Lumi

Launch via the installed console entry point or module runner:

```bash
lumi
# or:
python -m lumi.main
```

A Pygame window (`480×320` by default) will open displaying Lumi's geometric eyes in the `IDLE` (`NEUTRAL`) state.

---

## 5. Verifying Your First Conversation Turn

1. Speak **«سلام»** clearly into your microphone (in default `auto_vad` mode, Lumi shifts from `IDLE` to `LISTENING` on speech onset; or press `Space` to trigger/finalize manually).
2. Watch the eyes transition to `THINKING` briefly while Vosk transcribes and `PredefinedProvider` selects a Persian reply and `Emotion`.
3. Lumi switches to `SPEAKING` with `HAPPY` eyes and speaks a greeting such as **«سلام! خوبی؟»** through your speakers.
4. Press `Space` during `SPEAKING` at any time to interrupt playback (barge-in) and start speaking immediately, or close the window / press `Ctrl+C` to shut down cleanly.
