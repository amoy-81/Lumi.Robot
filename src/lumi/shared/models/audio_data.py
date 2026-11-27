"""Shared immutable audio buffer contract."""

from dataclasses import dataclass, field


@dataclass(frozen=True, slots=True)
class AudioData:
    """Immutable PCM audio buffer with validated format metadata."""

    samples: bytes = field(repr=False)
    sample_rate: int
    channels: int
    sample_width: int

    def __post_init__(self) -> None:
        if not isinstance(self.samples, bytes):
            raise TypeError(f"samples must be bytes, got {type(self.samples).__name__}")
        for field_name in ("sample_rate", "channels", "sample_width"):
            value = getattr(self, field_name)
            if isinstance(value, bool) or not isinstance(value, int):
                raise TypeError(f"{field_name} must be an int, got {value!r}")
        if self.sample_rate <= 0:
            raise ValueError(f"sample_rate must be positive, got {self.sample_rate}")
        if self.channels <= 0:
            raise ValueError(f"channels must be positive, got {self.channels}")
        if self.sample_width not in (1, 2, 4):
            raise ValueError(f"sample_width must be 1, 2, or 4 bytes, got {self.sample_width}")
        frame_size = self.channels * self.sample_width
        if len(self.samples) % frame_size != 0:
            raise ValueError(
                f"samples byte length ({len(self.samples)}) must be a multiple of "
                f"frame size ({frame_size})"
            )

    @property
    def duration_seconds(self) -> float:
        """Return total audio duration in seconds."""
        bytes_per_second = self.sample_rate * self.channels * self.sample_width
        return len(self.samples) / bytes_per_second
