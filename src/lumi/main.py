"""Runtime configuration, safe logging, and application lifecycle root."""

import argparse
import logging
import os
import re
import sys
import threading
from collections.abc import Callable, Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Final

from dotenv import dotenv_values

VALID_LOG_LEVELS: Final[frozenset[str]] = frozenset(
    {"DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"}
)
VALID_INTERACTION_MODES: Final[frozenset[str]] = frozenset({"auto_vad", "push_to_talk"})
VALID_CONVERSATION_PROVIDERS: Final[frozenset[str]] = frozenset({"predefined", "openai"})

_INT_PATTERN: Final[re.Pattern[str]] = re.compile(r"[+-]?[0-9]+")
_LUMI_LOGGER_NAME: Final[str] = "lumi"
_MANAGED_HANDLER_ATTR: Final[str] = "_lumi_managed"
_DEFAULT_JOIN_TIMEOUT_SECONDS: Final[float] = 5.0


@dataclass(frozen=True, slots=True)
class RuntimeConfig:
    """Immutable, validated runtime configuration for Lumi."""

    log_level: str = "INFO"
    interaction_mode: str = "auto_vad"
    vosk_model_path: str = "models/vosk-model-small-fa"
    espeak_bin: str = "espeak-ng"
    espeak_voice: str = "fa"
    audio_input_device: str | None = None
    audio_output_device: str | None = None
    face_width: int = 480
    face_height: int = 320
    face_fps: int = 60
    conversation_provider: str = "predefined"

    def __post_init__(self) -> None:
        if not isinstance(self.log_level, str):
            raise TypeError(f"log_level must be a string, got {self.log_level!r}")
        normalized_level = self.log_level.strip().upper()
        if normalized_level not in VALID_LOG_LEVELS:
            raise ValueError(
                f"log_level must be one of {sorted(VALID_LOG_LEVELS)}, got {self.log_level!r}"
            )
        object.__setattr__(self, "log_level", normalized_level)

        if self.interaction_mode not in VALID_INTERACTION_MODES:
            raise ValueError(
                f"interaction_mode must be one of {sorted(VALID_INTERACTION_MODES)}, "
                f"got {self.interaction_mode!r}"
            )

        if self.conversation_provider not in VALID_CONVERSATION_PROVIDERS:
            raise ValueError(
                f"conversation_provider must be one of {sorted(VALID_CONVERSATION_PROVIDERS)}, "
                f"got {self.conversation_provider!r}"
            )

        for field_name in ("vosk_model_path", "espeak_bin", "espeak_voice"):
            value = getattr(self, field_name)
            if not isinstance(value, str) or not value.strip():
                raise ValueError(f"{field_name} must be a non-empty string, got {value!r}")

        for device_field in ("audio_input_device", "audio_output_device"):
            device = getattr(self, device_field)
            if device is not None:
                if not isinstance(device, str):
                    raise TypeError(f"{device_field} must be a string or None, got {device!r}")
                object.__setattr__(self, device_field, device.strip() or None)

        for dim_field in ("face_width", "face_height", "face_fps"):
            dim_value = getattr(self, dim_field)
            if isinstance(dim_value, bool) or not isinstance(dim_value, int) or dim_value <= 0:
                raise ValueError(f"{dim_field} must be a positive integer, got {dim_value!r}")


def _parse_positive_int(key: str, raw: str | None) -> int:
    if raw is None:
        raise ValueError(f"{key} must be a positive integer, got None")
    stripped = raw.strip()
    if not stripped or not _INT_PATTERN.fullmatch(stripped):
        raise ValueError(f"{key} must be a positive integer, got {raw!r}")
    value = int(stripped)
    if value <= 0:
        raise ValueError(f"{key} must be a positive integer, got {raw!r}")
    return value


def _parse_required_str(key: str, raw: str | None) -> str:
    if raw is None or not raw.strip():
        raise ValueError(f"{key} must be a non-empty string, got {raw!r}")
    return raw.strip()


def _parse_optional_device(_key: str, raw: str | None) -> str | None:
    if raw is None:
        return None
    stripped = raw.strip()
    return stripped or None


_ENV_SPECS: Final[dict[str, tuple[str, Callable[[str, str | None], Any]]]] = {
    "LUMI_LOG_LEVEL": ("log_level", lambda k, v: _parse_required_str(k, v).upper()),
    "LUMI_INTERACTION_MODE": ("interaction_mode", _parse_required_str),
    "LUMI_VOSK_MODEL_PATH": ("vosk_model_path", _parse_required_str),
    "LUMI_ESPEAK_BIN": ("espeak_bin", _parse_required_str),
    "LUMI_ESPEAK_VOICE": ("espeak_voice", _parse_required_str),
    "LUMI_AUDIO_INPUT_DEVICE": ("audio_input_device", _parse_optional_device),
    "LUMI_AUDIO_OUTPUT_DEVICE": ("audio_output_device", _parse_optional_device),
    "LUMI_FACE_WIDTH": ("face_width", _parse_positive_int),
    "LUMI_FACE_HEIGHT": ("face_height", _parse_positive_int),
    "LUMI_FACE_FPS": ("face_fps", _parse_positive_int),
    "LUMI_CONVERSATION_PROVIDER": ("conversation_provider", _parse_required_str),
}


def load_runtime_config(env_file: Path | None = None) -> RuntimeConfig:
    """Load and validate RuntimeConfig from defaults, optional .env file, and os.environ."""
    target_env = Path(".env") if env_file is None else Path(env_file)
    merged: dict[str, str | None] = {}
    if target_env.is_file():
        merged.update(dotenv_values(target_env))

    for env_key in _ENV_SPECS:
        if env_key in os.environ:
            merged[env_key] = os.environ[env_key]

    config_kwargs: dict[str, Any] = {}
    for env_key, (field_name, parser) in _ENV_SPECS.items():
        if env_key in merged:
            config_kwargs[field_name] = parser(env_key, merged[env_key])

    return RuntimeConfig(**config_kwargs)


def configure_logging(level: str = "INFO") -> logging.Logger:
    """Configure stdlib logging for the 'lumi' logger without duplicating handlers."""
    if not isinstance(level, str):
        raise TypeError(f"Unsupported log level {level!r}; expected string")
    normalized = level.strip().upper()
    if normalized not in VALID_LOG_LEVELS:
        raise ValueError(
            f"Unsupported log level {level!r}; expected one of {sorted(VALID_LOG_LEVELS)}"
        )

    logger = logging.getLogger(_LUMI_LOGGER_NAME)
    logger.setLevel(getattr(logging, normalized))

    if not any(getattr(handler, _MANAGED_HANDLER_ATTR, False) for handler in logger.handlers):
        handler = logging.StreamHandler()
        handler.setFormatter(
            logging.Formatter("%(asctime)s | %(levelname)s | %(name)s | %(message)s")
        )
        setattr(handler, _MANAGED_HANDLER_ATTR, True)
        logger.addHandler(handler)

    return logger


def run_app(
    config: RuntimeConfig,
    controller_runner: Callable[[threading.Event], None],
    face_runner: Callable[[Callable[[], None]], None],
    teardown: Callable[[], None] | None = None,
) -> int:
    """Run controller worker thread alongside main-thread face runner with safe teardown."""
    logger = logging.getLogger(_LUMI_LOGGER_NAME)
    logger.info(
        "Starting Lumi lifecycle (mode=%s, provider=%s, face=%dx%d@%dfps)",
        config.interaction_mode,
        config.conversation_provider,
        config.face_width,
        config.face_height,
        config.face_fps,
    )

    stop_event = threading.Event()
    worker_errors: list[BaseException] = []

    def _run_worker() -> None:
        try:
            controller_runner(stop_event)
        except Exception as exc:
            worker_errors.append(exc)
            logger.exception("Controller worker exited with an unhandled error")
            stop_event.set()

    worker_thread = threading.Thread(
        target=_run_worker,
        name="lumi-controller",
        daemon=False,
    )

    face_failed = False
    worker_thread.start()
    try:
        face_runner(stop_event.set)
    except KeyboardInterrupt:
        logger.info("Shutdown requested via KeyboardInterrupt")
    except Exception:
        face_failed = True
        logger.exception("Face runner exited with an unhandled error")
    finally:
        stop_event.set()
        worker_thread.join(timeout=_DEFAULT_JOIN_TIMEOUT_SECONDS)
        if worker_thread.is_alive():
            logger.warning(
                "Controller worker thread '%s' did not exit within %.1fs",
                worker_thread.name,
                _DEFAULT_JOIN_TIMEOUT_SECONDS,
            )
        if teardown is not None:
            try:
                teardown()
            except Exception:
                face_failed = True
                logger.exception("Teardown callback raised an unhandled error")

    if worker_errors or face_failed or worker_thread.is_alive():
        return 1
    return 0


def _idle_controller_runner(stop_event: threading.Event) -> None:
    """Placeholder worker until FEAT-05 wires RobotController."""
    stop_event.wait()


def _idle_face_runner(request_stop: Callable[[], None]) -> None:
    """Placeholder main-thread runner until FEAT-04 wires FaceService."""
    idle_wait = threading.Event()
    try:
        while not idle_wait.wait(timeout=0.2):
            pass
    finally:
        request_stop()


def main(argv: Sequence[str] | None = None) -> int:
    """CLI entry point for the Lumi composition root."""
    parser = argparse.ArgumentParser(prog="lumi", description="Lumi desktop companion robot")
    parser.add_argument(
        "--check-config",
        action="store_true",
        help="Validate runtime configuration and exit without launching the UI.",
    )
    args = parser.parse_args(list(argv) if argv is not None else None)

    try:
        config = load_runtime_config()
    except ValueError as exc:
        print(f"Configuration error: {exc}", file=sys.stderr)
        return 1

    logger = configure_logging(config.log_level)
    logger.info(
        "Loaded runtime configuration (log_level=%s, mode=%s, provider=%s, face=%dx%d@%dfps)",
        config.log_level,
        config.interaction_mode,
        config.conversation_provider,
        config.face_width,
        config.face_height,
        config.face_fps,
    )

    if args.check_config:
        return 0

    return run_app(
        config=config,
        controller_runner=_idle_controller_runner,
        face_runner=_idle_face_runner,
    )


if __name__ == "__main__":
    raise SystemExit(main())
