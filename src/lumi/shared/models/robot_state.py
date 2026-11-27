"""Shared immutable robot state contract."""

from dataclasses import dataclass

from lumi.shared.enums.emotion import Emotion
from lumi.shared.enums.robot_activity import RobotActivity


@dataclass(frozen=True, slots=True)
class RobotState:
    """Immutable snapshot of the robot's current activity and emotion."""

    activity: RobotActivity = RobotActivity.IDLE
    emotion: Emotion = Emotion.NEUTRAL
