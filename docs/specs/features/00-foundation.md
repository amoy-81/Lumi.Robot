# Feature 00 — Project Foundation, Shared Contracts & Composition Root

**Feature Identifier:** `FEAT-00`  
**Layer Focus:** `pyproject.toml`, `src/lumi/shared/`, `src/lumi/main.py`  
**Deliverable:** Installable `lumi` Python package with strict module boundaries, cross-module data contracts, configuration loading, and startup/shutdown composition root  

---

## 1. Overview & Business Value

Before implementing audio capture, speech engines, conversation rules, or facial rendering, Lumi needs a clean, enforceable package skeleton. This foundation establishes the `src/lumi` layout, `pyproject.toml` packaging (including JSON data assets), shared immutable contracts, and the `main.py` composition root.

Completing `FEAT-00` guarantees that `audio`, `speech`, `conversation`, `face`, and `controller` can be developed and unit-tested independently using dependency injection and fakes without circular imports or third-party leakage.

---

## 2. Approaches Considered (Design Selection)

During specification design, three documentation/structuring approaches were evaluated:

1. **Architecture-Aligned Vertical Breakdown (`FEAT-00`..`FEAT-06`) — Selected:** One spec per architectural boundary (`Foundation`, `Audio`, `Speech`, `Conversation`, `Face`, `RobotController`, `Testing & Pi Readiness`). Mirrors the clean modular structure of the brief and maps 1:1 to phased implementation plans.
2. **Minimal 4-Module Bundle:** Merging foundation, controller, and testing into the four module specs. Rejected because shared contracts, thread boundaries, and packaging/Pi gates become scattered and harder to verify.
3. **Full Engineering Guides Upfront:** Writing developer how-to guides (`00..08`) alongside feature specs before any code exists. Rejected as premature; developer guides are better authored once implementation patterns settle.

---

## 3. Package Layout & Packaging (`pyproject.toml`)

### 3.1 Repository Tree
Preserve the approved `src`-layout namespace `lumi`:

```text
Lumi.Robot/
├── pyproject.toml
├── README.md
├── .env.example
├── .gitignore
├── docs/
│   ├── specs/features/
│   └── plans/
├── src/
│   └── lumi/
│       ├── __init__.py
│       ├── main.py
│       ├── shared/
│       │   ├── __init__.py
│       │   ├── models/
│       │   │   ├── __init__.py
│       │   │   ├── robot_state.py
│       │   │   └── audio_data.py
│       │   └── enums/
│       │       ├── __init__.py
│       │       ├── emotion.py
│       │       └── robot_activity.py
│       ├── controller/
│       │   ├── __init__.py
│       │   └── robot_controller.py
│       └── modules/
│           ├── __init__.py
│           ├── audio/
│           ├── speech/
│           ├── conversation/
│           └── face/
└── tests/
```

### 3.2 Packaging Specification
- **Python Baseline:** `requires-python = ">=3.11"` (modern typing, `asyncio.TaskGroup`/timeouts, `tomllib`, `StrEnum`).
- **Build Backend:** `setuptools>=68` via `setuptools.build_meta`.
- **Entry Point:** `[project.scripts]` exposes `lumi = "lumi.main:main"`.
- **MVP Runtime Dependencies:**
  - `sounddevice` (Audio I/O via PortAudio)
  - `numpy` (lightweight PCM RMS/array handling for VAD and `sounddevice` buffers)
  - `vosk` (offline Persian STT)
  - `pygame` (desktop geometric eye renderer and event loop)
  - `python-dotenv` (optional `.env` loading in `main.py` — or minimal stdlib `.env` parser if zero-extra-dep preferred; `python-dotenv` is small and standard)
- **Dev Dependencies (`[project.optional-dependencies] dev`):** `pytest`, `pytest-asyncio`, `ruff`.
- **Deferred Dependencies:** `openai` SDK must **not** be included in MVP dependencies.
- **Package Data:** JSON files under `lumi/modules/conversation/providers/predefined/data/*.json` must be declared in `[tool.setuptools.package-data]` and loaded via `importlib.resources.files(...)` (never fragile relative filesystem paths).

---

## 4. Shared Contracts & Enums (`src/lumi/shared/`)

`shared` contains **only** data structures and enums that cross module boundaries:

### 4.1 Enums (`shared/enums/`)
```python
from enum import StrEnum

class Emotion(StrEnum):
    NEUTRAL = "neutral"
    HAPPY = "happy"
    SAD = "sad"
    ANGRY = "angry"
    SURPRISED = "surprised"

class RobotActivity(StrEnum):
    IDLE = "idle"
    LISTENING = "listening"
    THINKING = "thinking"
    SPEAKING = "speaking"
```

### 4.2 Models (`shared/models/`)
```python
from dataclasses import dataclass
from lumi.shared.enums import Emotion, RobotActivity

@dataclass(frozen=True, slots=True)
class RobotState:
    activity: RobotActivity = RobotActivity.IDLE
    emotion: Emotion = Emotion.NEUTRAL

@dataclass(frozen=True, slots=True)
class AudioData:
    samples: bytes          # Raw linear PCM bytes (little-endian signed int16 by default)
    sample_rate: int        # Hz, e.g. 16000
    channels: int           # e.g. 1 (mono)
    sample_width: int       # Bytes per sample, e.g. 2 (16-bit)

    def __post_init__(self) -> None:
        if self.sample_rate <= 0:
            raise ValueError("sample_rate must be positive")
        if self.channels <= 0:
            raise ValueError("channels must be positive")
        if self.sample_width not in (1, 2, 4):
            raise ValueError("sample_width must be 1, 2, or 4 bytes")
        frame_bytes = self.channels * self.sample_width
        if len(self.samples) % frame_bytes != 0:
            raise ValueError("samples byte length must align with channels * sample_width")

    @property
    def duration_seconds(self) -> float:
        bytes_per_second = self.sample_rate * self.channels * self.sample_width
        return len(self.samples) / bytes_per_second
```

---

## 5. Configuration & Composition Root (`main.py`)

### 5.1 Environment Configuration (`.env.example`)
Each module defines its own typed config dataclass (`AudioConfig`, `SpeechConfig`, `FaceConfig`, etc.) constructed in `main.py` from environment variables with sensible defaults:
- `LUMI_LOG_LEVEL=INFO`
- `LUMI_INTERACTION_MODE=auto_vad` (`auto_vad` | `push_to_talk`)
- `LUMI_VOSK_MODEL_PATH=models/vosk-model-small-fa`
- `LUMI_ESPEAK_VOICE=fa`
- `LUMI_AUDIO_INPUT_DEVICE=` (empty = system default)
- `LUMI_AUDIO_OUTPUT_DEVICE=` (empty = system default)
- `LUMI_FACE_WIDTH=480`
- `LUMI_FACE_HEIGHT=320`
- `LUMI_CONVERSATION_PROVIDER=predefined`

### 5.2 Composition Root Responsibilities (`main.py`)
1. Configure structured logging (`logging` standard library; never log raw audio bytes or future API keys).
2. Load module configs from env/defaults.
3. Instantiate concrete module services and inject providers (`VoskSTTProvider`, `EspeakTTSProvider`, `PredefinedProvider`).
4. Instantiate `RobotController` with injected service interfaces.
5. Launch controller worker thread and enter `FaceService.run()` on the main thread.
6. Catch `SIGINT` / window-close exit signals and guarantee deterministic resource teardown (`controller.stop()`, audio stream close, Pygame quit).

---

## 6. Risks & Explicit Assumptions

- **Risk — Accidental Cross-Module Coupling:** Developers importing `audio_config` or `conversation_models` inside `face` or `controller`. *Mitigation:* Static import-boundary check in `tests/` (or `ruff` rules) asserting modules only import from `lumi.shared`, stdlib, or their own package.
- **Assumption:** Logging uses Python's built-in `logging` module rather than third-party logging frameworks to minimize footprint for future Pi deployment.

---

## 7. Acceptance Criteria

1. `pip install -e .[dev]` (and `pip install .`) succeeds in a clean Python 3.11+ environment and exposes the `lumi` entry point.
2. `intents.json` and `responses.json` are packaged inside the wheel and accessible via `importlib.resources` without relying on the current working directory.
3. `RobotState`, `AudioData`, `Emotion`, and `RobotActivity` reject invalid audio metadata and are immutable (`frozen=True`).
4. No file under `src/lumi/modules/<mod_a>/` imports from `src/lumi/modules/<mod_b>/`.
5. `main.py` initializes and shuts down cleanly without leaving dangling threads or open audio streams.
