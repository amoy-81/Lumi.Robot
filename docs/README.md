# Lumi Documentation

Welcome to the engineering and architectural documentation for **Lumi** (`lumi-robot`) — an offline-first, modular Persian desktop companion robot built with Python, `sounddevice`, Vosk, eSpeak NG, and Pygame, designed to evolve cleanly toward a Raspberry Pi Zero 2 W hardware target.

---

## Engineering & Developer Guides

| File | Description |
|---|---|
| [00-getting-started.md](file:///C:/Users/NIAVARAN/Desktop/projects/Lumi/Lumi.Robot/docs/00-getting-started.md) | Local development setup, Python `3.11+`, `espeak-ng`, offline Vosk Persian model setup, and running `lumi`. |
| [01-project-structure.md](file:///C:/Users/NIAVARAN/Desktop/projects/Lumi/Lumi.Robot/docs/01-project-structure.md) | `src/lumi` layout, module isolation rules, dependency graph, and component breakdown. |
| [02-python-architecture-and-conventions.md](file:///C:/Users/NIAVARAN/Desktop/projects/Lumi/Lumi.Robot/docs/02-python-architecture-and-conventions.md) | Dependency injection, protocol boundaries, threading/`asyncio` isolation, typing, and packaging rules. |
| [03-audio-and-offline-speech.md](file:///C:/Users/NIAVARAN/Desktop/projects/Lumi/Lumi.Robot/docs/03-audio-and-offline-speech.md) | `sounddevice` capture/playback, Auto-VAD + `Space` trigger, Vosk Persian STT, and eSpeak NG WAV TTS. |
| [04-conversation-and-face-engine.md](file:///C:/Users/NIAVARAN/Desktop/projects/Lumi/Lumi.Robot/docs/04-conversation-and-face-engine.md) | Persian text normalization, JSON rule engine, 20-turn RAM context, `OpenAIProvider` seam, and Pygame geometric eyes. |
| [05-adding-a-feature.md](file:///C:/Users/NIAVARAN/Desktop/projects/Lumi/Lumi.Robot/docs/05-adding-a-feature.md) | Step-by-step developer guide for adding a module, provider, intent, or emotion without breaking boundaries. |
| [06-testing.md](file:///C:/Users/NIAVARAN/Desktop/projects/Lumi/Lumi.Robot/docs/06-testing.md) | Test pyramid, fake-driven `pytest` unit/integration suite, `SDL_VIDEODRIVER=dummy`, and packaging verification. |
| [07-environments-and-config.md](file:///C:/Users/NIAVARAN/Desktop/projects/Lumi/Lumi.Robot/docs/07-environments-and-config.md) | `.env` configuration hierarchy, key reference, and desktop vs. Raspberry Pi Zero 2 W runtime profiles. |
| [08-manual-test-checklist.md](file:///C:/Users/NIAVARAN/Desktop/projects/Lumi/Lumi.Robot/docs/08-manual-test-checklist.md) | End-to-end PC verification checklist (Persian voice turns, animations, barge-in) and Pi hardware readiness gate. |

---

## Subdirectories

- **[specs/features/](file:///C:/Users/NIAVARAN/Desktop/projects/Lumi/Lumi.Robot/docs/specs/features/README.md)**: Functional and technical specifications for each Lumi capability (`FEAT-00` Foundation to `FEAT-06` Testing & Pi Readiness).
- **[plans/](file:///C:/Users/NIAVARAN/Desktop/projects/Lumi/Lumi.Robot/docs/plans/README.md)**: Task-by-task implementation plans for feature development.
