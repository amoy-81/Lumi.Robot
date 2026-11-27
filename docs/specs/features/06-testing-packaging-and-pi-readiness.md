# Feature 06 — Testing, Packaging Verification & Pi Readiness

**Feature Identifier:** `FEAT-06`  
**Layer Focus:** `tests/`, `pyproject.toml`, `README.md`, Target Hardware Validation  
**Deliverable:** Isolated fake-driven `pytest` suite, PC E2E smoke test, offline/packaging verification, and Raspberry Pi Zero 2 W readiness criteria  

---

## 1. Overview & Business Value

Because Lumi combines hardware I/O (`sounddevice`), native binaries (`espeak-ng`), offline ML models (`vosk`), and a GUI loop (`pygame`), automated tests must run reliably **without** physical microphones, speakers, monitors, or internet access. At the same time, before deploying to a Raspberry Pi Zero 2 W, Lumi requires measured validation rather than assumptions.

This feature defines the automated test architecture for the PC MVP and the explicit hardware validation gate for future Pi deployment.

---

## 2. Test Suite Architecture (`tests/`)

Matches the approved test structure using `pytest` and `pytest-asyncio`:

| Test File | Scope & Doubles Used | Key Verifications |
|---|---|---|
| `test_audio_service.py` | Fake `sounddevice` streams | Auto-VAD speech onset + pre-roll, silence timeout, short-burst rejection (`<0.25s`), chunked playback cancellation, missing device error. |
| `test_speech_to_text.py` | Fake Vosk recognizer/model | Valid `16kHz/1ch/int16` audio transcription, empty string on silence, format mismatch rejection, missing model path fail-fast. |
| `test_text_to_speech.py` | Mocked `subprocess.run` returning WAV bytes | Valid WAV-to-`AudioData` parsing, empty text guard, missing `espeak-ng` error, timeout handling, zero speaker side effects. |
| `test_conversation_service.py` | Fake `ConversationProvider` | Async `respond()` contract, context update sequencing, error propagation without corrupting history. |
| `test_conversation_context.py` | Real `ConversationContextManager` | Max `20`-message sliding bound, `clear_history()`, `pending_intent` lifecycle, metadata isolation. |
| `test_predefined_provider.py` | Real `PredefinedProvider` + packaged JSON | End-to-end greeting/wellbeing/name/thanks/farewell/unknown cases, anti-repetition variety across repeated turns. |
| `test_predefined_rule_engine.py` | Real `PredefinedRuleEngine` | Contextual `pending_intent` follow-up matching and fallback rule activation. |
| `test_predefined_intent_matcher.py` | Real `PredefinedIntentMatcher` | Persian normalization (`ي`/`ی`, `ك`/`ک`, ZWNJ, diacritics, punctuation) and intent scoring. |
| `test_face_service.py` | `SDL_VIDEODRIVER=dummy` + fake clock `dt` | Emotion vs. activity layering (`SPEAKING + HAPPY`), blink cadence, smooth interpolation, thread-safe `set_state()`, `QUIT`/`SPACE` callbacks. |
| `test_robot_controller.py` | Fake `Audio`, `STT`, `TTS`, `Conversation`, `Face` | Full state transition trace, empty STT recovery, timeout/error recovery, barge-in cancellation, clean shutdown. |

### 2.1 Structural & Packaging Checks
- **Architecture Boundary Test:** Automated AST/import test verifying no module under `lumi/modules/<X>` imports any sibling `lumi/modules/<Y>`, and `lumi/shared` imports no modules or controller code.
- **Package Installation Test:** Build/install wheel (`pip install .`) into a fresh virtual environment and verify `lumi` console script + `importlib.resources` loading of `intents.json` and `responses.json` works from an unrelated working directory.
- **Offline Execution Smoke Test:** Run a fake-audio / real-predefined-conversation / headless-face turn with network disabled (or verifying zero network socket calls) and confirm full pipeline completion.
- **PC E2E Smoke Test & Persian Quality Check (Manual/Hardware-Present):** Documented checklist in [08-manual-test-checklist.md](file:///C:/Users/NIAVARAN/Desktop/projects/Lumi/Lumi.Robot/docs/08-manual-test-checklist.md) and `README.md` for testing real mic → Vosk Persian → Predefined → eSpeak NG → Pygame window + speakers across a representative 8–10 phrase Persian corpus (greetings, wellbeing, name, thanks, farewell, follow-ups, unknown input).

---

## 3. Documentation Deliverables (`README.md`)

`README.md` must provide accurate, reproducible instructions for:
1. Installing Python `3.11+` and system dependencies (`espeak-ng`, PortAudio on Linux if needed).
2. Downloading and placing the offline Persian Vosk model (`models/vosk-model-small-fa`), with verified license and checksum/source notes.
3. Configuring `.env` from `.env.example` (device selection, `LUMI_INTERACTION_MODE`, display size).
4. Launching Lumi (`lumi` or `python -m lumi.main`) and running `pytest`.

---

## 4. Raspberry Pi Zero 2 W Readiness Gate (Post-MVP Hardware Validation)

**Policy:** *Do not claim Raspberry Pi compatibility until measured on actual Pi Zero 2 W hardware.*

Before declaring Pi support, measure and document:
1. **Memory Budget:** Pi Zero 2 W has `512 MB` total RAM. Measure peak RSS of `Vosk small-fa` + `Pygame` + Python runtime (target `< 280 MB` RSS without swap thrashing).
2. **CPU & Latency Budget:** Measure STT recognition latency, eSpeak synthesis time, and Pygame frame rate at `320×240` (`target_fps=20..30`) on ARM64 Cortex-A53.
3. **Display Driver:** Validate Pygame/SDL2 rendering target on headless Linux (`kmsdrm` / `fbcon` vs minimal X11/Wayland) for the chosen 2–3" SPI/DSI screen.
4. **Audio Hardware:** Verify ALSA/PortAudio stability at `16000 Hz` (or confirm whether software resampling is needed inside `AudioService` for the chosen USB/I2S mic & speaker HAT).

---

## 5. Acceptance Criteria

1. Full `pytest` suite passes offline with zero physical audio/display hardware attached (CI/headless safe).
2. Automated import-boundary test enforces zero cross-module imports.
3. Installing from wheel in a clean temp directory successfully loads `intents.json` and `responses.json`.
4. PC E2E smoke test passes with real microphone, Vosk model, eSpeak NG, speakers, and Pygame face window.
5. `README.md` documents exact setup, model acquisition, config, and test commands; Pi support remains explicitly marked "pending hardware validation" until benchmarked.
