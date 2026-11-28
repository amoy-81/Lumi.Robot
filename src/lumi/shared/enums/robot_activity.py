"""Shared robot activity state contract for Lumi."""

from enum import StrEnum


class RobotActivity(StrEnum):
    """High-level operational activity states of the robot."""

    IDLE = "idle"
    LISTENING = "listening"
    THINKING = "thinking"
    SPEAKING = "speaking"
