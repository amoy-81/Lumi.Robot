# Lumi (`lumi-robot`)

Offline-first Persian desktop companion robot built in Python (`3.11+`).

See [docs/00-getting-started.md](docs/00-getting-started.md) for full prerequisites, platform notes, and walkthroughs.

## Setup

1. **Create and activate a Python 3.11+ virtual environment:**

   ```bash
   python -m venv .venv
   # Windows (PowerShell / cmd):
   .venv\Scripts\activate
   # Linux / macOS:
   source .venv/bin/activate

   pip install -e .[dev]
   ```

2. **Install `espeak-ng` (offline Persian TTS):**
   - **Windows:** Install from the official `espeak-ng` release installer and ensure `espeak-ng.exe` is on `PATH`.
   - **Linux (Ubuntu/Debian/Raspberry Pi OS):** `sudo apt install espeak-ng portaudio19-dev`

3. **Download the offline Persian Vosk STT model:**
   - Download `vosk-model-small-fa-*` from AlphaCephei Vosk models and extract it to `models/vosk-model-small-fa/` (containing `am/`, `conf/`, `graph/`, etc.).

4. **Configure environment variables:**

   ```bash
   cp .env.example .env
   ```

   Adjust `LUMI_VOSK_MODEL_PATH`, `LUMI_ESPEAK_BIN`, or audio devices in `.env` if needed.

## Running Lumi

```bash
lumi
# or:
python -m lumi.main
```

## Running Tests

```bash
pytest
```
