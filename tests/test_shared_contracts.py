from dataclasses import FrozenInstanceError

import pytest

from lumi.shared import AudioData, Emotion, RobotActivity, RobotState


def test_emotion_enum_values():
    assert [e.value for e in Emotion] == ["neutral", "happy", "sad", "angry", "surprised"]


def test_robot_activity_enum_values():
    assert [a.value for a in RobotActivity] == ["idle", "listening", "thinking", "speaking"]


def test_robot_state_defaults_and_immutability():
    state = RobotState()
    assert state.activity is RobotActivity.IDLE
    assert state.emotion is Emotion.NEUTRAL
    assert not hasattr(state, "__dict__")

    happy_speaking = RobotState(activity=RobotActivity.SPEAKING, emotion=Emotion.HAPPY)
    assert happy_speaking == RobotState(RobotActivity.SPEAKING, Emotion.HAPPY)
    assert hash(happy_speaking) == hash(RobotState(RobotActivity.SPEAKING, Emotion.HAPPY))

    with pytest.raises(FrozenInstanceError):
        state.emotion = Emotion.HAPPY  # type: ignore[misc]


def test_audio_data_valid_and_duration():
    # 0.5s of 16kHz mono int16 = 16000 bytes
    sample_bytes = b"\xab\xcd" * 8000
    audio = AudioData(samples=sample_bytes, sample_rate=16000, channels=1, sample_width=2)
    assert audio.duration_seconds == pytest.approx(0.5)
    assert not hasattr(audio, "__dict__")

    audio_repr = repr(audio)
    assert "samples" not in audio_repr
    assert "\\xab" not in audio_repr
    assert "sample_rate=16000" in audio_repr

    # 0.5s of 16kHz stereo int16 = 32000 bytes
    stereo_16 = AudioData(samples=b"\x00" * 32000, sample_rate=16000, channels=2, sample_width=2)
    assert stereo_16.duration_seconds == pytest.approx(0.5)

    # 0.25s of 48kHz stereo int32 = 96000 bytes
    stereo_32 = AudioData(samples=b"\x00" * 96000, sample_rate=48000, channels=2, sample_width=4)
    assert stereo_32.duration_seconds == pytest.approx(0.25)

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
        (b"\x00\x00\x00", 16000, 1, 2),  # misaligned for 2-byte frame
        (b"\x00\x00", 16000, 2, 2),  # misaligned for stereo 16-bit (4-byte frame)
    ],
)
def test_audio_data_rejects_invalid_metadata_or_alignment(
    samples: bytes, sample_rate: int, channels: int, sample_width: int
):
    with pytest.raises(ValueError):
        AudioData(
            samples=samples,
            sample_rate=sample_rate,
            channels=channels,
            sample_width=sample_width,
        )


@pytest.mark.parametrize(
    ("samples", "sample_rate", "channels", "sample_width"),
    [
        (bytearray(b"\x00\x00"), 16000, 1, 2),
        (memoryview(b"\x00\x00"), 16000, 1, 2),
        ("not-bytes", 16000, 1, 2),
        (None, 16000, 1, 2),
        (b"\x00\x00", True, 1, 2),
        (b"\x00\x00", False, 1, 2),
        (b"\x00\x00", 16000, True, 2),
        (b"\x00\x00", 16000, 1, True),
        (b"\x00\x00", 16000.0, 1, 2),
    ],
)
def test_audio_data_rejects_invalid_types(
    samples: object, sample_rate: object, channels: object, sample_width: object
):
    with pytest.raises(TypeError):
        AudioData(
            samples=samples,  # type: ignore[arg-type]
            sample_rate=sample_rate,  # type: ignore[arg-type]
            channels=channels,  # type: ignore[arg-type]
            sample_width=sample_width,  # type: ignore[arg-type]
        )
