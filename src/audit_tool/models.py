"""Shared, engine-agnostic data models."""
from dataclasses import dataclass


@dataclass(frozen=True)
class Span:
    """Identifier occurrence, with zero-based half-open character offsets."""

    start: int
    end: int
    label: str
    text: str
    source: str = "regex"

    def __post_init__(self) -> None:
        if self.start < 0 or self.end <= self.start:
            raise ValueError("Invalid span offsets")


@dataclass(frozen=True)
class PipelineResult:
    original_text: str
    transformed_text: str
    spans: tuple[Span, ...]
    remaining_original_identifiers: tuple[str, ...]

    @property
    def detected_count(self) -> int:
        return len(self.spans)

    @property
    def unchanged_identifier_count(self) -> int:
        """Exact-string persistence indicator; NOT a re-identification risk score."""
        return len(self.remaining_original_identifiers)
