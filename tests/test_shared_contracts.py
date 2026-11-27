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
