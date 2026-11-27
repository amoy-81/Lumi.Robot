# FEAT-00: Project Foundation, Shared Contracts & Composition Root Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build and verify the installable `lumi` Python package (`src/lumi/`), immutable cross-module shared contracts, packaged JSON resource wiring, architecture boundary enforcement, and clean `main.py` startup/shutdown lifecycle.

**Architecture:** Standard Python `src`-layout package (`lumi`) with strict lateral isolation: `lumi.shared` holds only immutable contracts and enums (`AudioData`, `RobotState`, `Emotion`, `RobotActivity`); `lumi.modules.{audio,speech,conversation,face}` have zero cross-module imports; `lumi.main` serves as the composition root loading environment config and managing worker/UI lifecycle teardown.

**Tech Stack:** Python `>=3.11`, `setuptools>=68`, `sounddevice`, `numpy`, `vosk`, `pygame`, `python-dotenv`, `pytest`, `pytest-asyncio`, `ruff`.

**Spec:** [docs/specs/features/00-foundation.md](file:///C:/Users/NIAVARAN/Desktop/projects/Lumi/Lumi.Robot/docs/specs/features/00-foundation.md)

---

## Global Constraints

- `requires-python = ">=3.11"` with `setuptools>=68` (`setuptools.build_meta`) and console script `lumi = "lumi.main:main"`.
- Runtime dependencies limited to `sounddevice`, `numpy`, `vosk`, `pygame`, `python-dotenv`; `openai` SDK must **not** be included in MVP dependencies.
- Dev dependencies: `pytest`, `pytest-asyncio`, `ruff`.
- Strict module isolation: no file under `src/lumi/modules/<mod_a>/` may import from `src/lumi/modules/<mod_b>/` or `lumi.controller`.
- `lumi.shared` contains only cross-module contracts and enums (`Emotion`, `RobotActivity`, `RobotState`, `AudioData`), all immutable (`frozen=True`, `slots=True`).
- JSON resources under `lumi/modules/conversation/providers/predefined/data/*.json` must be packaged as package-data and loaded via `importlib.resources.files(...)`.
- Logging uses Python stdlib `logging`; never log raw audio bytes or future secrets.

---

## Review Focus

1. **Invalid `AudioData` metadata & frame misalignment:** `sample_rate <= 0`, `channels <= 0`, unsupported `sample_width` (anything outside `(1, 2, 4)`), or `samples` byte length not divisible by `channels * sample_width` must raise `ValueError`; empty `b""` audio must report `duration_seconds == 0.0` without `ZeroDivisionError`. (Pinned in Task 3: `tests/test_shared_contracts.py`)
2. **Invalid environment variable values at startup:** Non-numeric `LUMI_FACE_WIDTH`/`LUMI_FACE_HEIGHT`, non-positive dimensions, or unsupported `LUMI_INTERACTION_MODE` / `LUMI_LOG_LEVEL` must fail fast with an explicit `ValueError` in `load_runtime_config()`. (Pinned in Task 5: `tests/test_main_lifecycle.py`)
3. **JSON resources missing from installed wheel / CWD dependence:** Importing and reading `intents.json` and `responses.json` from an unrelated working directory (`tmp_path`) and inspecting a built wheel must find both files inside the package. (Pinned in Task 4: `tests/test_package_resources.py`)
4. **Accidental cross-module or reverse `shared` imports:** AST import verification must catch sibling-module imports (`modules.audio` importing `modules.speech`) and `shared` importing `modules` or `controller`. (Pinned in Task 4: `tests/test_architecture_boundaries.py`)
5. **Dangling worker threads or skipped teardown on error:** An exception in the background worker or stop signal during `run_app()` must still execute shutdown callbacks and exit cleanly with zero live `lumi-` threads. (Pinned in Task 5: `tests/test_main_lifecycle.py`)

---

### Task 1: Project Scaffolding, Packaging & Base Package Skeleton

**Files:**
- Create: `pyproject.toml`
- Create: `.gitignore`
- Create: `.env.example`
- Create: `README.md`
- Create: `src/lumi/__init__.py`
- Create: `src/lumi/controller/__init__.py`
- Create: `src/lumi/modules/__init__.py`
- Create: `src/lumi/modules/audio/__init__.py`
- Create: `src/lumi/modules/speech/__init__.py`
- Create: `src/lumi/modules/conversation/__init__.py`
- Create: `src/lumi/modules/face/__init__.py`
- Create: `tests/__init__.py`

**Interfaces:**
- Consumes: None (root setup)
- Produces: Installable `lumi` package (`pip install -e .[dev]`) with Python `3.11+` floor, `lumi` script entry point, and package namespace tree.

- [ ] **Step 1: Verify Python 3.11+ virtual environment and Git repository**

Run: `python --version` (on Windows if system default is `<3.11`, use `py -3.11 -m venv .venv` and activate `.venv` before running subsequent commands; if `.git` is not initialized yet, run `git init`).
Expected: Active interpreter reports `Python 3.11.x` or higher, and `git status` succeeds.

- [ ] **Step 2: Create `pyproject.toml`, `.gitignore`, `.env.example`, and `README.md`**

Create `pyproject.toml`:
```toml
[build-system]
requires = ["setuptools>=68"]
build-backend = "setuptools.build_meta"

[project]
name = "lumi-robot"
version = "0.1.0"
description = "Offline-first Persian desktop companion robot"
readme = "README.md"
requires-python = ">=3.11"
dependencies = [
    "sounddevice>=0.4.6",
    "numpy>=1.26",
    "vosk>=0.3.45",
    "pygame>=2.5",
    "python-dotenv>=1.0",
]

[project.optional-dependencies]
dev = [
    "pytest>=8.0",
    "pytest-asyncio>=0.23",
    "ruff>=0.4",
]

[project.scripts]
lumi = "lumi.main:main"

[tool.setuptools.packages.find]
where = ["src"]

[tool.setuptools.package-data]
"lumi.modules.conversation.providers.predefined" = ["data/*.json"]

[tool.pytest.ini_options]
testpaths = ["tests"]
asyncio_mode = "auto"

[tool.ruff]
line-length = 100
target-version = "py311"
```

Create `.gitignore` (ignoring `.venv/`, `__pycache__/`, `*.pyc`, `.pytest_cache/`, `.ruff_cache/`, `dist/`, `build/`, `*.egg-info/`, `.env`, `models/`).

Create `.env.example` with all baseline keys from `00-foundation.md` §5.1 (`LUMI_LOG_LEVEL`, `LUMI_INTERACTION_MODE`, `LUMI_VOSK_MODEL_PATH`, `LUMI_ESPEAK_BIN`, `LUMI_ESPEAK_VOICE`, `LUMI_AUDIO_INPUT_DEVICE`, `LUMI_AUDIO_OUTPUT_DEVICE`, `LUMI_FACE_WIDTH`, `LUMI_FACE_HEIGHT`, `LUMI_FACE_FPS`, `LUMI_CONVERSATION_PROVIDER`).

Create `README.md` with setup, `espeak-ng` + Vosk Persian model acquisition notes, `.env` copy instructions, `lumi` launch command, and `pytest` command (linking to `docs/00-getting-started.md`).

- [ ] **Step 3: Create base package `__init__.py` files**

Create empty/docstring `__init__.py` markers for `src/lumi/__init__.py` (`__version__ = "0.1.0"`), `src/lumi/controller/__init__.py`, `src/lumi/modules/__init__.py`, `src/lumi/modules/{audio,speech,conversation,face}/__init__.py`, and `tests/__init__.py`.

- [ ] **Step 4: Verify editable install and package import**

Run: `pip install --no-build-isolation -e .[dev] && python -c "import lumi; print(lumi.__version__)"` (or `pip install -e .[dev]` with network).
Expected: Package installs cleanly and prints `0.1.0`.

- [ ] **Step 5: Commit**

```bash
git add pyproject.toml .gitignore .env.example README.md src/ tests/
git commit -m "feat(foundation): scaffold lumi package layout and pyproject.toml"
```

---

### Task 2: Shared Enums (`Emotion`, `RobotActivity`) & `RobotState`

**Files:**
- Create: `src/lumi/shared/__init__.py`
- Create: `src/lumi/shared/enums/__init__.py`
- Create: `src/lumi/shared/enums/emotion.py`
- Create: `src/lumi/shared/enums/robot_activity.py`
- Create: `src/lumi/shared/models/__init__.py`
- Create: `src/lumi/shared/models/robot_state.py`
- Create: `tests/test_shared_contracts.py`

**Interfaces:**
- Consumes: None
- Produces:
  - `Emotion(StrEnum)`: `NEUTRAL`, `HAPPY`, `SAD`, `ANGRY`, `SURPRISED`
  - `RobotActivity(StrEnum)`: `IDLE`, `LISTENING`, `THINKING`, `SPEAKING`
  - `RobotState(frozen=True, slots=True)`: `(activity: RobotActivity = RobotActivity.IDLE, emotion: Emotion = Emotion.NEUTRAL)`

- [ ] **Step 1: Write failing tests for enums and `RobotState`**

Create `tests/test_shared_contracts.py`:
```python
from dataclasses import FrozenInstanceError
import pytest

from lumi.shared import Emotion, RobotActivity, RobotState


def test_emotion_enum_values():
    assert [e.value for e in Emotion] == ["neutral", "happy", "sad", "angry", "surprised"]


def test_robot_activity_enum_values():
    assert [a.value for a in RobotActivity] == ["idle", "listening", "thinking", "speaking"]


def test_robot_state_defaults_and_immutability():
    state = RobotState()
    assert state.activity is RobotActivity.IDLE
    assert state.emotion is Emotion.NEUTRAL

    happy_speaking = RobotState(activity=RobotActivity.SPEAKING, emotion=Emotion.HAPPY)
    assert happy_speaking == RobotState(RobotActivity.SPEAKING, Emotion.HAPPY)
    assert hash(happy_speaking) == hash(RobotState(RobotActivity.SPEAKING, Emotion.HAPPY))

    with pytest.raises(FrozenInstanceError):
        state.emotion = Emotion.HAPPY  # type: ignore[misc]
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_shared_contracts.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'lumi.shared'`.

- [ ] **Step 3: Implement `Emotion`, `RobotActivity`, `RobotState`, and package exports**

- In `src/lumi/shared/enums/emotion.py`: define `class Emotion(StrEnum)` with `NEUTRAL`, `HAPPY`, `SAD`, `ANGRY`, `SURPRISED`.
- In `src/lumi/shared/enums/robot_activity.py`: define `class RobotActivity(StrEnum)` with `IDLE`, `LISTENING`, `THINKING`, `SPEAKING`.
- In `src/lumi/shared/models/robot_state.py`: define `@dataclass(frozen=True, slots=True) class RobotState` with `activity: RobotActivity = RobotActivity.IDLE` and `emotion: Emotion = Emotion.NEUTRAL`.
- Re-export from `shared/enums/__init__.py`, `shared/models/__init__.py`, and `shared/__init__.py`.

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/test_shared_contracts.py -v`
Expected: `3 passed`.

- [ ] **Step 5: Commit**

```bash
git add src/lumi/shared/ tests/test_shared_contracts.py
git commit -m "feat(shared): add Emotion, RobotActivity, and immutable RobotState"
```

---

### Task 3: Shared `AudioData` Contract & Format Validation

**Files:**
- Create: `src/lumi/shared/models/audio_data.py`
- Modify: `src/lumi/shared/models/__init__.py`
- Modify: `src/lumi/shared/__init__.py`
- Modify: `tests/test_shared_contracts.py`

**Interfaces:**
- Consumes: None
- Produces:
  - `AudioData(samples: bytes, sample_rate: int, channels: int, sample_width: int)` (`frozen=True`, `slots=True`)
  - `AudioData.duration_seconds -> float`

- [ ] **Step 1: Write failing tests for `AudioData` (including Review Focus #1)**

Append to `tests/test_shared_contracts.py`:
```python
from lumi.shared import AudioData


def test_audio_data_valid_and_duration():
    # 0.5s of 16kHz mono int16 = 16000 bytes
    audio = AudioData(samples=b"\x00\x00" * 8000, sample_rate=16000, channels=1, sample_width=2)
    assert audio.duration_seconds == pytest.approx(0.5)

    empty = AudioData(samples=b"", sample_rate=16000, channels=1, sample_width=2)
    assert empty.duration_seconds == 0.0

    with pytest.raises(FrozenInstanceError):
        audio.sample_rate = 8000  # type: ignore[misc]


@pytest.mark.parametrize(
    ("samples", "sample_rate", "channels", "sample_width"),
    [
        (b"\x00\x00", 0, 1, 2),
        (b"\x00\x00", -16000, 1, 2),
        (b"\x00\x00", 16000, 0, 2),
        (b"\x00\x00", 16000, 1, 3),
        (b"\x00\x00\x00", 16000, 1, 2),   # misaligned for 2-byte frame
        (b"\x00\x00", 16000, 2, 2),       # misaligned for stereo 16-bit (4-byte frame)
    ],
)
def test_audio_data_rejects_invalid_metadata_or_alignment(
    samples: bytes, sample_rate: int, channels: int, sample_width: int
):
    with pytest.raises(ValueError):
        AudioData(samples=samples, sample_rate=sample_rate, channels=channels, sample_width=sample_width)
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_shared_contracts.py -v`
Expected: FAIL with `ImportError: cannot import name 'AudioData' from 'lumi.shared'`.

- [ ] **Step 3: Implement `AudioData` in `src/lumi/shared/models/audio_data.py` and export**

Implement `@dataclass(frozen=True, slots=True) class AudioData` with `__post_init__` validating `sample_rate > 0`, `channels > 0`, `sample_width in (1, 2, 4)`, and `len(samples) % (channels * sample_width) == 0`, plus `@property def duration_seconds(self) -> float`. Export `AudioData` in `shared/models/__init__.py` and `shared/__init__.py`.

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/test_shared_contracts.py -v`
Expected: `10 passed`.

- [ ] **Step 5: Commit**

```bash
git add src/lumi/shared/ tests/test_shared_contracts.py
git commit -m "feat(shared): add validated immutable AudioData contract"
```

---

### Task 4: Packaged JSON Resources & Architecture Boundary Enforcement

**Files:**
- Create: `src/lumi/modules/conversation/providers/__init__.py`
- Create: `src/lumi/modules/conversation/providers/predefined/__init__.py`
- Create: `src/lumi/modules/conversation/providers/predefined/data/__init__.py`
- Create: `src/lumi/modules/conversation/providers/predefined/data/intents.json`
- Create: `src/lumi/modules/conversation/providers/predefined/data/responses.json`
- Create: `tests/test_package_resources.py`
- Create: `tests/test_architecture_boundaries.py`

**Interfaces:**
- Consumes: `pyproject.toml` package-data configuration
- Produces:
  - Packaged `intents.json` and `responses.json` loadable via `importlib.resources`
  - AST-based cross-module import boundary test (`find_boundary_violations(src_root: Path) -> list[str]`)

- [ ] **Step 1: Write failing tests for JSON package resources and import boundaries (Review Focus #3 & #4)**

Create `tests/test_package_resources.py`:
```python
from importlib import resources
import json
import subprocess
import sys
import zipfile
from pathlib import Path


def test_predefined_json_resources_load_independent_of_cwd(tmp_path: Path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    data_pkg = resources.files("lumi.modules.conversation.providers.predefined.data")

    intents = json.loads((data_pkg / "intents.json").read_text(encoding="utf-8"))
    responses = json.loads((data_pkg / "responses.json").read_text(encoding="utf-8"))

    assert isinstance(intents, dict) and "intents" in intents
    assert isinstance(responses, dict) and "responses" in responses


def test_wheel_includes_predefined_json_resources(tmp_path: Path):
    repo_root = Path(__file__).resolve().parents[1]
    subprocess.run(
        [sys.executable, "-m", "pip", "wheel", str(repo_root), "--no-deps", "--no-build-isolation", "-w", str(tmp_path)],
        check=True,
    )
    wheels = list(tmp_path.glob("lumi_robot-*.whl"))
    assert len(wheels) == 1
    with zipfile.ZipFile(wheels[0]) as zf:
        names = set(zf.namelist())
    assert "lumi/modules/conversation/providers/predefined/data/intents.json" in names
    assert "lumi/modules/conversation/providers/predefined/data/responses.json" in names
```

Create `tests/test_architecture_boundaries.py`:
```python
from pathlib import Path

def test_repo_has_zero_architecture_boundary_violations():
    src_root = Path(__file__).resolve().parents[1] / "src" / "lumi"
    assert find_boundary_violations(src_root) == []


def test_detector_flags_cross_module_and_shared_violations(tmp_path: Path):
    (tmp_path / "modules" / "audio").mkdir(parents=True)
    (tmp_path / "modules" / "speech").mkdir(parents=True)
    (tmp_path / "shared").mkdir(parents=True)

    (tmp_path / "modules" / "audio" / "bad.py").write_text(
        "from lumi.modules.speech import speech_to_text\n", encoding="utf-8"
    )
    (tmp_path / "shared" / "leak.py").write_text(
        "import lumi.controller.robot_controller\n", encoding="utf-8"
    )

    violations = find_boundary_violations(tmp_path)
    assert len(violations) == 2
```
*(In Step 3, implement `find_boundary_violations(src_root: Path) -> list[str]` in `tests/test_architecture_boundaries.py` using `ast.parse` to inspect `ast.Import` and `ast.ImportFrom` nodes: flag any file under `modules/<mod_a>/` importing `lumi.modules.<mod_b>` (`mod_b != mod_a`) or `lumi.controller`, and any file under `shared/` importing `lumi.modules` or `lumi.controller`.)*

- [ ] **Step 2: Run tests to verify they fail**

Run: `pytest tests/test_package_resources.py tests/test_architecture_boundaries.py -v`
Expected: FAIL (`ModuleNotFoundError` for `predefined.data` package and missing boundary check implementation).

- [ ] **Step 3: Create predefined package tree, starter JSON files, and implement boundary test**

- Create `__init__.py` under `providers/`, `predefined/`, and `predefined/data/`.
- Create minimal valid starter `intents.json` (`{"intents": []}`) and `responses.json` (`{"responses": {}}`) — full Persian catalog will be authored in `FEAT-03`.
- Complete `find_boundary_violations(src_root: Path) -> list[str]` in `tests/test_architecture_boundaries.py` handling both `ast.Import` (`import lumi.modules.speech`) and `ast.ImportFrom` (`from lumi.modules.speech import ...`, plus relative imports resolving above module root).

- [ ] **Step 4: Run tests to verify they pass**

Run: `pytest tests/test_package_resources.py tests/test_architecture_boundaries.py -v`
Expected: `4 passed` (both `.json` files present in wheel and readable from `tmp_path`, zero boundary violations).

- [ ] **Step 5: Commit**

```bash
git add src/lumi/modules/conversation/ tests/test_package_resources.py tests/test_architecture_boundaries.py
git commit -m "feat(foundation): add packaged JSON data skeleton and import boundary tests"
```

---

### Task 5: Runtime Config, Safe Logging & `main.py` Composition Root Lifecycle

**Files:**
- Create: `src/lumi/main.py`
- Create: `tests/test_main_lifecycle.py`

**Interfaces:**
- Consumes: `Emotion`, `RobotActivity`, `RobotState`
- Produces:
  - `RuntimeConfig` dataclass (`frozen=True, slots=True`)
  - `load_runtime_config(env_file: Path | None = None) -> RuntimeConfig`
  - `configure_logging(level: str = "INFO") -> logging.Logger`
  - `run_app(config: RuntimeConfig, controller_runner: Callable[[threading.Event], None], face_runner: Callable[[Callable[[], None]], None], teardown: Callable[[], None] | None = None) -> int`
  - `main(argv: Sequence[str] | None = None) -> int` (supports `--check-config` for non-GUI verification)

- [ ] **Step 1: Write failing tests for config validation, safe logging, and lifecycle teardown (Review Focus #2 & #5)**

Create `tests/test_main_lifecycle.py`:
```python
from collections.abc import Callable
import logging
import threading
import time
from pathlib import Path
import pytest

from lumi.main import RuntimeConfig, configure_logging, load_runtime_config, main, run_app


def test_load_runtime_config_defaults_and_env_override(tmp_path: Path, monkeypatch):
    env_file = tmp_path / ".env"
    env_file.write_text("LUMI_FACE_WIDTH=320\nLUMI_FACE_HEIGHT=240\n", encoding="utf-8")
    monkeypatch.setenv("LUMI_INTERACTION_MODE", "push_to_talk")

    cfg = load_runtime_config(env_file=env_file)
    assert isinstance(cfg, RuntimeConfig)
    assert cfg.face_width == 320
    assert cfg.face_height == 240
    assert cfg.interaction_mode == "push_to_talk"
    assert cfg.conversation_provider == "predefined"


@pytest.mark.parametrize(
    ("key", "value"),
    [
        ("LUMI_FACE_WIDTH", "not-an-int"),
        ("LUMI_FACE_WIDTH", "-10"),
        ("LUMI_FACE_HEIGHT", "0"),
        ("LUMI_FACE_FPS", "0"),
        ("LUMI_INTERACTION_MODE", "invalid_mode"),
        ("LUMI_LOG_LEVEL", "VERBOSE"),
    ],
)
def test_load_runtime_config_rejects_invalid_values(monkeypatch, key: str, value: str):
    monkeypatch.setenv(key, value)
    with pytest.raises(ValueError):
        load_runtime_config()


def test_run_app_joins_worker_thread_and_runs_teardown_on_worker_error():
    events: list[str] = []

    def failing_worker(stop_event: threading.Event) -> None:
        events.append("worker_started")
        raise RuntimeError("boom")

    def fake_face(request_stop: Callable[[], None]) -> None:
        time.sleep(0.05)
        events.append("face_exiting")
        request_stop()

    def teardown() -> None:
        events.append("teardown")

    exit_code = run_app(
        config=RuntimeConfig(),
        controller_runner=failing_worker,
        face_runner=fake_face,
        teardown=teardown,
    )
    assert exit_code == 1
    assert "teardown" in events
    assert not any(t.name.startswith("lumi-") and t.is_alive() for t in threading.enumerate())


def test_run_app_clean_shutdown_leaves_no_dangling_threads():
    worker_stopped = threading.Event()

    def worker(stop_event: threading.Event) -> None:
        stop_event.wait(timeout=2.0)
        worker_stopped.set()

    def fake_face(request_stop: Callable[[], None]) -> None:
        request_stop()

    exit_code = run_app(config=RuntimeConfig(), controller_runner=worker, face_runner=fake_face)
    assert exit_code == 0
    assert worker_stopped.is_set()
    assert not any(t.name.startswith("lumi-") and t.is_alive() for t in threading.enumerate())


def test_main_check_config_flag_exits_zero(tmp_path: Path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    assert main(["--check-config"]) == 0
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_main_lifecycle.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'lumi.main'`.

- [ ] **Step 3: Implement `src/lumi/main.py`**

Implement:
- `RuntimeConfig`: frozen dataclass with validated fields matching `.env.example` (`log_level`, `interaction_mode`, `vosk_model_path`, `espeak_bin`, `espeak_voice`, `audio_input_device`, `audio_output_device`, `face_width`, `face_height`, `face_fps`, `conversation_provider`).
- `load_runtime_config(env_file: Path | None = None) -> RuntimeConfig`: loads `.env` via `dotenv.dotenv_values` (if file exists, without mutating process env globally for cleaner tests, letting `os.environ` override `.env`), parses integers/strings strictly, raises explicit `ValueError` on invalid values.
- `configure_logging(level: str = "INFO") -> logging.Logger`: configures `lumi` logger on stdlib `logging`.
- `run_app(...) -> int`: spawns `threading.Thread(name="lumi-controller", ...)` capturing worker errors cleanly, runs `face_runner(request_stop)` on the calling (main) thread, handles `KeyboardInterrupt`, always sets `stop_event`, joins the worker thread with timeout, and always invokes `teardown()` in `finally`. Returns `0` on clean exit, `1` if worker raised an unhandled error.
- `main(argv: Sequence[str] | None = None) -> int`: parses `--check-config` via `argparse`, loads config, configures logging, and either returns `0` immediately (`--check-config`) or calls `run_app()` with a placeholder worker/UI runner (waiting on `stop_event` until `SIGINT`/`KeyboardInterrupt`) until `FEAT-01..05` wire concrete services.

- [ ] **Step 4: Run test to verify it passes and run full suite + lint**

Run:
```bash
pytest -v
ruff check src tests
```
Expected: All tests across `test_shared_contracts.py`, `test_package_resources.py`, `test_architecture_boundaries.py`, and `test_main_lifecycle.py` pass (`100%`), and `ruff check` reports `All checks passed!`.

- [ ] **Step 5: Commit**

```bash
git add src/lumi/main.py tests/test_main_lifecycle.py
git commit -m "feat(foundation): implement runtime config, safe logging, and main lifecycle composition root"
```
