# 06 — Testing Strategy & Guidelines

This document defines Lumi's automated testing strategy. All unit and controller integration tests must run **completely offline** and **without physical microphones, speakers, or an interactive display**.

---

## 1. Test Pyramid

```text
          ▲
         / \     PC End-to-End Smoke Test (Real Mic, Vosk, eSpeak NG, Pygame, Speakers)
        /───\
       /     \    Controller Integration & Packaging Tests (Fakes + Wheel Resource Check)
      /───────\
     /         \   Module Unit Tests (pytest + Fakes, Headless SDL, Zero Hardware)
    ─────────────
```

---

## 2. Module Unit Tests (`tests/`)

Each module is tested independently using small in-memory fakes/doubles rather than real hardware:

| Test File | Focus | Hardware / External Isolation |
|---|---|---|
| `test_audio_service.py` | VAD onset, pre-roll, silence timeout, noise filter, chunked cancel | Fake `sounddevice` input/output streams |
| `test_speech_to_text.py` | Format checks, transcript extraction, missing model fail-fast | Fake Vosk model/recognizer |
| `test_text_to_speech.py` | WAV parsing into `AudioData`, empty-text guard, timeouts | Mocked `subprocess.run` returning in-memory WAV bytes |
| `test_conversation_service.py` | Async `respond()`, history update order, error pass-through | Fake `ConversationProvider` |
| `test_conversation_context.py` | `20`-message cap, `clear_history()`, `pending_intent`, metadata | Pure in-memory unit test |
| `test_predefined_intent_matcher.py` | Persian normalization (`ي`/`ی`, `ك`/`ک`, ZWNJ, punctuation) | Packaged `intents.json` |
| `test_predefined_rule_engine.py` | Contextual `pending_intent` follow-ups & fallback | Pure unit test |
| `test_predefined_provider.py` | Starter intents, emotion mapping, anti-repetition variety | Packaged `intents.json` + `responses.json` |
| `test_face_service.py` | Emotion×Activity layering, blink timer, lerp smoothness, callbacks | `SDL_VIDEODRIVER=dummy` + fake `dt` |

---

## 3. Controller Integration, Boundary & Packaging Tests

- **`test_robot_controller.py`:** Injects fake `Audio`, `STT`, `TTS`, `Conversation`, and `Face` services to verify:
  - Full `IDLE -> LISTENING -> THINKING -> SPEAKING -> IDLE` trace
  - Empty STT short-circuiting back to `IDLE`
  - Error recovery on `Audio`/`STT`/`Conversation`/`TTS` failures without hanging
  - `Space` barge-in cancelling `SPEAKING` and entering `LISTENING`
  - Clean worker thread shutdown (`stop()`)
- **Import Boundary Test:** AST check verifying no module under `lumi/modules/<A>` imports any sibling `lumi/modules/<B>` or `lumi.controller`.
- **Wheel Packaging Test:** Install built package (`pip install .`) into an isolated environment and confirm `intents.json` and `responses.json` load via `importlib.resources` from an arbitrary working directory.

---

## 4. Running the Tests

```bash
# Run full test suite (headless-safe)
pytest

# Run with verbose output and specific test file
pytest -v tests/test_robot_controller.py

# Headless Pygame explicitly forced (useful in CI/Linux SSH)
SDL_VIDEODRIVER=dummy pytest tests/test_face_service.py
```
