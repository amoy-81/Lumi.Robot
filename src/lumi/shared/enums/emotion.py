"""Shared emotional state contract for Lumi."""

from enum import StrEnum


class Emotion(StrEnum):
    """Facial and expressive emotional states supported across Lumi modules."""

    NEUTRAL = "neutral"
    HAPPY = "happy"
    SAD = "sad"
    ANGRY = "angry"
    SURPRISED = "surprised"
