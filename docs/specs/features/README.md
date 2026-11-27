# Feature Specifications (`docs/specs/features`)

This directory contains the functional, architectural, and technical specifications for **Lumi** — an offline-first Persian desktop companion robot (Python MVP) designed to evolve toward a Raspberry Pi Zero 2 W hardware target without rewriting core boundaries.

These specifications translate [LUMI_PROJECT_BRIEF.md](file:///C:/Users/NIAVARAN/Downloads/LUMI_PROJECT_BRIEF.md) into concrete, modular feature specs (`FEAT-00` through `FEAT-06`) ready for phased implementation planning in `docs/plans/`.

---

## Feature Catalog

| ID | Specification | Summary |
|---|---|---|
| **FEAT-00** | [00-foundation.md](file:///C:/Users/NIAVARAN/Desktop/projects/Lumi/Lumi.Robot/docs/specs/features/00-foundation.md) | `src/lumi` package layout, `pyproject.toml` packaging, `shared/` contracts & enums, configuration, and `main.py` composition root. |
| **FEAT-01** | [01-audio-io-and-vad.md](file:///C:/Users/NIAVARAN/Desktop/projects/Lumi/Lumi.Robot/docs/specs/features/01-audio-io-and-vad.md) | `sounddevice` microphone capture and speaker playback, device selection, 16kHz mono PCM contract, Auto-VAD + Spacebar trigger. |
| **FEAT-02** | [02-offline-persian-speech.md](file:///C:/Users/NIAVARAN/Desktop/projects/Lumi/Lumi.Robot/docs/specs/features/02-offline-persian-speech.md) | Replaceable STT/TTS interfaces with offline Vosk Persian recognition and eSpeak NG WAV synthesis. |
| **FEAT-03** | [03-conversation-and-context.md](file:///C:/Users/NIAVARAN/Desktop/projects/Lumi/Lumi.Robot/docs/specs/features/03-conversation-and-context.md) | Async conversation service, Persian normalization, JSON intents/responses, `PredefinedProvider`, 20-turn RAM context, and `OpenAIProvider` seam. |
| **FEAT-04** | [04-face-renderer-and-animations.md](file:///C:/Users/NIAVARAN/Desktop/projects/Lumi/Lumi.Robot/docs/specs/features/04-face-renderer-and-animations.md) | Pygame geometric eyes without external assets, 5 emotions × 4 activities layering, blinking, smooth transitions, and UI thread loop. |
| **FEAT-05** | [05-robot-controller-and-loop.md](file:///C:/Users/NIAVARAN/Desktop/projects/Lumi/Lumi.Robot/docs/specs/features/05-robot-controller-and-loop.md) | `RobotController` state machine, half-duplex interaction flow, worker/UI concurrency isolation, timeouts, and error recovery. |
| **FEAT-06** | [06-testing-packaging-and-pi-readiness.md](file:///C:/Users/NIAVARAN/Desktop/projects/Lumi/Lumi.Robot/docs/specs/features/06-testing-packaging-and-pi-readiness.md) | Fake-driven `pytest` unit/integration suite, E2E smoke test, JSON package-data verification, and Raspberry Pi Zero 2 W validation gates. |

---

## Module Independence & Dependency Rules

Lumi enforces strict module isolation across its four functional modules:

```text
                    ┌──────────────────┐
                    │     main.py      │  (Composition Root)
                    └────────┬─────────┘
                             │ constructs & wires
                             ▼
                    ┌──────────────────┐
                    │ RobotController  │  (Orchestration & State Transitions)
                    └──┬───┬───────┬──┬┘
                       │   │       │  │
        ┌──────────────┘   │       │  └──────────────┐
        ▼                  ▼       ▼                 ▼
   ┌─────────┐      ┌────────┐ ┌──────────────┐ ┌────────┐
   │  Audio  │      │ Speech │ │ Conversation │ │  Face  │
   └────┬────┘      └───┬────┘ └──────┬───────┘ └───┬────┘
        │               │             │             │
        └───────────────┴──────┬──────┴─────────────┘
                               ▼
                      ┌─────────────────┐
                      │  lumi.shared    │  (AudioData, RobotState, Emotion, RobotActivity)
                      └─────────────────┘
```

- **Zero Cross-Module Imports:** `audio`, `speech`, `conversation`, and `face` **must never** import or call each other.
- **Shared Minimalism:** `lumi.shared` holds only cross-module contracts and enums (`AudioData`, `RobotState`, `Emotion`, `RobotActivity`). Module-specific models (such as `ConversationContext`) stay local to their owning module.
- **Provider Isolation:** Third-party engines (`sounddevice`, `vosk`, `espeak-ng`, `pygame`) remain encapsulated inside their owning module behind explicit Python protocols/ABCs.

---

## Baseline Decisions & Assumptions

| Decision | MVP Baseline Choice | Rationale & Tradeoff |
|---|---|---|
| **Python & Packaging** | Python `3.11+`, `setuptools` via `pyproject.toml` | Reliable `importlib.resources` JSON packaging and wide library wheel support on Windows & ARM64 Linux. |
| **Audio Format** | `16000 Hz`, Mono (`1` ch), `int16` PCM | Matches Vosk's native input format without resampling overhead; eSpeak WAV output is normalized cleanly. |
| **Interaction Trigger** | Auto-VAD loop (default) + `Space` manual trigger/barge-in | Hands-free companion feel by default, with deterministic keyboard fallback/override for noisy rooms or testing. |
| **Duplex Policy** | Half-duplex (mic capture paused while speaking) | Prevents speaker-to-mic acoustic echo loops without requiring hardware AEC in MVP. |
| **Concurrency Model** | Pygame on **Main Thread**; `RobotController` async loop on **Worker Thread** | Respects SDL/Pygame OS event-loop constraints while keeping blocking audio/STT/TTS calls from freezing animations. |
| **Display Baseline** | `480×320` PC window scaled from `320×240` logical grid | Cleanly previews 2–3" Raspberry Pi SPI/DSI display proportions on desktop. |
| **Cloud AI (`OpenAI`)** | Interface seam only (`NotImplementedError` stub) | Preserves offline-first MVP and zero SDK bloat while keeping future LLM swap trivial. |
