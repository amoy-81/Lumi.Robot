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

    happy_speaking = RobotState(activity=RobotActivity.SPEAKING, emotion=Emotion.HAPPY)
    assert happy_speaking == RobotState(RobotActivity.SPEAKING, Emotion.HAPPY)
    assert hash(happy_speaking) == hash(RobotState(RobotActivity.SPEAKING, Emotion.HAPPY))

    with pytest.raises(FrozenInstanceError):
        state.emotion = Emotion.HAPPY  # type: ignore[misc]


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
