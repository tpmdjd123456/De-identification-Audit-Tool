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


@dataclass(frozen=True)
class TransformationRecord:
    label: str
    category: str
    strategy: str
    original: str
    replacement: str
    start: int
    end: int
    fallback_reason: str | None = None


@dataclass(frozen=True)
class DocumentTransformation:
    document_id: str
    output_text: str
    config: dict
    records: tuple[TransformationRecord, ...]
    date_offset_days: int


# Interoperability helpers: preserve the existing Span and app API; normalize
# Presidio/Qwen/OPF dict records only at the transformation boundary.
from typing import Iterable, Mapping, Any


def span_from_entity(entity: Mapping[str, Any], text: str, *, source: str = "detector") -> Span:
    """Convert a detector record with {start,end,type} or {start,end,label}."""
    if "type" not in entity and "label" not in entity:
        raise KeyError("Identifier entity requires 'type' or 'label'")
    start, end = int(entity["start"]), int(entity["end"])
    if start < 0 or end <= start or end > len(text):
        raise ValueError(f"Invalid entity offsets {start}:{end} for document of length {len(text)}")
    label = entity.get("type", entity.get("label"))
    # A missing label becomes fail-closed unknown. A bad provided surface
    # value must not be silently ignored.
    value = text[start:end] if entity.get("text") is None else str(entity["text"])
    if value != text[start:end]:
        raise ValueError("Entity text does not match source text at offsets")
    return Span(start, end, "" if label is None else str(label), value,
                source=str(entity.get("source", source)))


def spans_from_entities(entities: Iterable[Mapping[str, Any]], text: str,
                        *, source: str = "detector") -> list[Span]:
    """Build sorted spans without silently discarding ambiguous overlaps."""
    return sorted((span_from_entity(row, text, source=source) for row in entities),
                  key=lambda span: (span.start, span.end))


def entity_from_span(span: Span) -> dict[str, Any]:
    return {"start": span.start, "end": span.end, "type": span.label,
            "text": span.text, "source": span.source}


def entities_from_spans(spans: Iterable[Span]) -> list[dict[str, Any]]:
    return [entity_from_span(span) for span in spans]
