import logging
import os
import threading
import time
from collections.abc import Callable
from dataclasses import FrozenInstanceError
from pathlib import Path

import pytest

from lumi.main import RuntimeConfig, configure_logging, load_runtime_config, main, run_app


def _clear_lumi_env(monkeypatch: pytest.MonkeyPatch) -> None:
    for key in list(os.environ):
        if key.startswith("LUMI_"):
            monkeypatch.delenv(key, raising=False)


def test_load_runtime_config_defaults_and_env_override(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
):
    _clear_lumi_env(monkeypatch)
    monkeypatch.chdir(tmp_path)
    env_file = tmp_path / ".env"
    env_file.write_text("LUMI_FACE_WIDTH=320\nLUMI_FACE_HEIGHT=240\n", encoding="utf-8")
    monkeypatch.setenv("LUMI_INTERACTION_MODE", "push_to_talk")

    cfg = load_runtime_config(env_file=env_file)
    assert isinstance(cfg, RuntimeConfig)
    assert cfg.log_level == "INFO"
    assert cfg.face_width == 320
    assert cfg.face_height == 240
    assert cfg.face_fps == 60
    assert cfg.interaction_mode == "push_to_talk"
    assert cfg.vosk_model_path == "models/vosk-model-small-fa"
    assert cfg.espeak_bin == "espeak-ng"
    assert cfg.espeak_voice == "fa"
    assert cfg.audio_input_device is None
    assert cfg.audio_output_device is None
    assert cfg.conversation_provider == "predefined"


def test_load_runtime_config_env_overrides_dotenv_and_normalizes_empty_devices(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
):
    _clear_lumi_env(monkeypatch)
    monkeypatch.chdir(tmp_path)
    env_file = tmp_path / ".env"
    env_file.write_text(
        (
            "LUMI_FACE_WIDTH=320\n"
            "LUMI_ESPEAK_VOICE=fa-latn\n"
            "LUMI_AUDIO_INPUT_DEVICE=hw:1\n"
            "LUMI_AUDIO_OUTPUT_DEVICE=plughw:0\n"
        ),
        encoding="utf-8",
    )
    monkeypatch.setenv("LUMI_FACE_WIDTH", "640")
    monkeypatch.setenv("LUMI_AUDIO_INPUT_DEVICE", "")
    monkeypatch.setenv("LUMI_AUDIO_OUTPUT_DEVICE", "   ")

    cfg = load_runtime_config(env_file=env_file)
    assert cfg.face_width == 640
    assert cfg.espeak_voice == "fa-latn"
    assert cfg.audio_input_device is None
    assert cfg.audio_output_device is None
    assert "LUMI_ESPEAK_VOICE" not in os.environ


def test_load_runtime_config_uses_cwd_dotenv_and_handles_missing_env_file(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
):
    _clear_lumi_env(monkeypatch)
    monkeypatch.chdir(tmp_path)

    default_cfg = load_runtime_config()
    assert default_cfg == RuntimeConfig()

    (tmp_path / ".env").write_text("LUMI_FACE_FPS=30\n", encoding="utf-8")
    cwd_cfg = load_runtime_config()
    assert cwd_cfg.face_fps == 30

    missing_cfg = load_runtime_config(env_file=tmp_path / "does-not-exist.env")
    assert missing_cfg == RuntimeConfig()


@pytest.mark.parametrize(
    ("key", "value"),
    [
        ("LUMI_FACE_WIDTH", "not-an-int"),
        ("LUMI_FACE_WIDTH", "-10"),
        ("LUMI_FACE_WIDTH", ""),
        ("LUMI_FACE_HEIGHT", "0"),
        ("LUMI_FACE_HEIGHT", "   "),
        ("LUMI_FACE_FPS", "0"),
        ("LUMI_FACE_FPS", "30.5"),
        ("LUMI_INTERACTION_MODE", "invalid_mode"),
        ("LUMI_LOG_LEVEL", "VERBOSE"),
        ("LUMI_CONVERSATION_PROVIDER", "anthropic"),
        ("LUMI_VOSK_MODEL_PATH", ""),
        ("LUMI_ESPEAK_BIN", "   "),
        ("LUMI_ESPEAK_VOICE", ""),
    ],
)
def test_load_runtime_config_rejects_invalid_values(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, key: str, value: str
):
    _clear_lumi_env(monkeypatch)
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv(key, value)
    with pytest.raises(ValueError):
        load_runtime_config()


def test_runtime_config_is_frozen_and_validates_direct_instantiation():
    cfg = RuntimeConfig()
    with pytest.raises(FrozenInstanceError):
        cfg.face_width = 800  # type: ignore[misc]

    for invalid_kwargs in [
        {"face_width": 0},
        {"face_height": -1},
        {"face_fps": 0},
        {"face_width": True},
        {"interaction_mode": "bad"},
        {"conversation_provider": "bad"},
        {"log_level": "VERBOSE"},
        {"vosk_model_path": "  "},
        {"espeak_bin": ""},
        {"espeak_voice": ""},
    ]:
        with pytest.raises(ValueError):
            RuntimeConfig(**invalid_kwargs)  # type: ignore[arg-type]


def test_configure_logging_avoids_duplicate_handlers_and_validates_level():
    lumi_logger = logging.getLogger("lumi")
    original_handlers = list(lumi_logger.handlers)
    original_level = lumi_logger.level
    lumi_logger.handlers.clear()
    try:
        logger = configure_logging("INFO")
        assert logger is lumi_logger
        assert logger.level == logging.INFO
        assert len(logger.handlers) == 1

        logger_again = configure_logging("debug")
        assert logger_again is lumi_logger
        assert logger_again.level == logging.DEBUG
        assert len(logger_again.handlers) == 1

        with pytest.raises(ValueError):
            configure_logging("VERBOSE")
    finally:
        lumi_logger.handlers[:] = original_handlers
        lumi_logger.setLevel(original_level)


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
    events: list[str] = []

    def worker(stop_event: threading.Event) -> None:
        stop_event.wait(timeout=2.0)
        worker_stopped.set()
        events.append("worker_exited")

    def fake_face(request_stop: Callable[[], None]) -> None:
        request_stop()

    exit_code = run_app(
        config=RuntimeConfig(),
        controller_runner=worker,
        face_runner=fake_face,
        teardown=lambda: events.append("teardown"),
    )
    assert exit_code == 0
    assert worker_stopped.is_set()
    assert events == ["worker_exited", "teardown"]
    assert not any(t.name.startswith("lumi-") and t.is_alive() for t in threading.enumerate())


def test_run_app_handles_keyboard_interrupt_and_face_exception_with_teardown():
    worker_stopped = threading.Event()
    teardowns: list[str] = []

    def worker(stop_event: threading.Event) -> None:
        stop_event.wait(timeout=2.0)
        worker_stopped.set()

    def interrupt_face(request_stop: Callable[[], None]) -> None:
        raise KeyboardInterrupt

    exit_code = run_app(
        config=RuntimeConfig(),
        controller_runner=worker,
        face_runner=interrupt_face,
        teardown=lambda: teardowns.append("kb"),
    )
    assert exit_code == 0
    assert worker_stopped.is_set()
    assert teardowns == ["kb"]
    assert not any(t.name.startswith("lumi-") and t.is_alive() for t in threading.enumerate())

    worker_stopped.clear()

    def crashing_face(request_stop: Callable[[], None]) -> None:
        raise RuntimeError("ui-crash")

    crash_code = run_app(
        config=RuntimeConfig(),
        controller_runner=worker,
        face_runner=crashing_face,
        teardown=lambda: teardowns.append("err"),
    )
    assert crash_code == 1
    assert worker_stopped.is_set()
    assert teardowns == ["kb", "err"]
    assert not any(t.name.startswith("lumi-") and t.is_alive() for t in threading.enumerate())


def test_main_check_config_flag_exits_zero(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    _clear_lumi_env(monkeypatch)
    monkeypatch.chdir(tmp_path)
    assert main(["--check-config"]) == 0


def test_main_check_config_logs_safe_summary_and_rejects_invalid_config(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    caplog: pytest.LogCaptureFixture,
    capsys: pytest.CaptureFixture[str],
):
    _clear_lumi_env(monkeypatch)
    monkeypatch.chdir(tmp_path)
    lumi_logger = logging.getLogger("lumi")
    original_handlers = list(lumi_logger.handlers)
    original_level = lumi_logger.level
    try:
        with caplog.at_level(logging.INFO, logger="lumi"):
            assert main(["--check-config"]) == 0
        assert "auto_vad" in caplog.text
        assert "predefined" in caplog.text
        assert "480x320" in caplog.text

        monkeypatch.setenv("LUMI_FACE_WIDTH", "not-an-int")
        assert main(["--check-config"]) == 1
        captured = capsys.readouterr()
        assert "LUMI_FACE_WIDTH" in captured.err
    finally:
        lumi_logger.handlers[:] = original_handlers
        lumi_logger.setLevel(original_level)
