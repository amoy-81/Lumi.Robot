# 02 — Python Architecture & Engineering Conventions

This document defines the coding standards, dependency injection patterns, concurrency rules, and module boundary conventions for the **Lumi** Python codebase.

---

## 1. Strict Module Isolation Rules

1. **Zero Lateral Imports:** No file in `src/lumi/modules/<module_a>/` may import from `src/lumi/modules/<module_b>/` or `src/lumi/controller/`.
2. **Internal Imports Allowed:** Files inside the same module (e.g., `predefined_provider.py` importing `predefined_rule_engine.py`) may import each other freely.
3. **Provider Encapsulation:** Third-party libraries (`sounddevice`, `vosk`, `pygame`) and OS subprocess invocations (`espeak-ng`) must stay inside their owning module. Never pass `pygame.Surface`, `vosk.KaldiRecognizer`, or `sounddevice` stream objects across module boundaries.
4. **Minimal `shared/`:** Keep `lumi.shared` restricted to `AudioData`, `RobotState`, `Emotion`, and `RobotActivity`. Do **not** place `ConversationContext`, audio device dicts, or Pygame colors in `shared/`.

---

## 2. Dependency Injection & Explicit Protocols

Lumi uses constructor-based dependency injection with Python `typing.Protocol` interfaces—no heavy DI container or dynamic plugin discovery framework.

```python
class RobotController:
    def __init__(
        self,
        audio: AudioServiceProtocol,
        stt: SpeechToTextProtocol,
        tts: TextToSpeechProtocol,
        conversation: ConversationServiceProtocol,
        face: FaceServiceProtocol,
        config: ControllerConfig | None = None,
    ) -> None:
        ...
```

- **Benefits:** Unit tests inject lightweight in-memory fakes for any subset of services with zero mocking magic.
- **Composition Root (`main.py`):** `main.py` is the only place that knows all concrete classes (`AudioService`, `VoskSTTProvider`, `EspeakTTSProvider`, `PredefinedProvider`, `FaceService`, `RobotController`).

---

## 3. Concurrency & Threading Rules

Pygame/SDL2 requires window creation, event polling, and display flips on the **OS main thread** on Windows and macOS/Linux. Blocking audio capture, Vosk inference, or `espeak-ng` subprocess calls on the main thread would freeze animations and cause "Not Responding" OS dialogs.

| Thread | Owner | Allowed Work |
|---|---|---|
| **Main Thread** | `FaceService.run()` | `pygame.event.get()`, `FaceAnimations.update(dt)`, `FaceRenderer.draw()`, `pygame.display.flip()`, dispatching lightweight callbacks (`on_quit`, `on_manual_trigger`). |
| **Controller Worker Thread** | `RobotController` (`asyncio` loop) | Turn orchestration, `await conversation.respond(...)`, `await asyncio.to_thread(...)` for blocking `AudioService`, `VoskSTTProvider`, and `EspeakTTSProvider` calls. |

### Cross-Thread Communication Rules
- `FaceService.set_state(state: RobotState)` updates an immutable `RobotState` behind a `threading.Lock` and returns immediately.
- `RobotController.on_manual_trigger()` / `stop()` notify the worker thread using `threading.Event` or `loop.call_soon_threadsafe(...)`—never blocking the UI thread waiting on audio or STT.

---

## 4. Python Style, Typing & Packaging Rules

- **Python Version:** `3.11+`. Use modern type annotations (`X | Y`, `list[str]`, `collections.abc.Callable`, `StrEnum`).
- **Value Objects:** Use `@dataclass(frozen=True, slots=True)` for immutable contracts (`AudioData`, `RobotState`, `ConversationReply`, `ConversationMessage`).
- **Naming:** Explicit `snake_case` filenames with module prefixes where helpful (e.g., `audio_service.py`, `vosk_stt_provider.py`, `predefined_rule_engine.py`).
- **Package Resources:** Always load JSON files (`intents.json`, `responses.json`) via `importlib.resources.files(...)` so installed wheels work regardless of current working directory.
- **Privacy & Logging:** Use Python stdlib `logging`. Never log raw `AudioData.samples` bytes or future API keys at `INFO` or `DEBUG` by default.
- **Keep It Simple:** Avoid microservices, ORMs/databases, dynamic plugin entry-point scanning, or speculative abstractions not needed by the MVP.
