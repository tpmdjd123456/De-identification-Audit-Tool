"""End-to-end pipeline and honest, baseline-only residual checks."""
import re
from typing import Mapping
from .detector import RegexDetector
from .models import PipelineResult, Span
from .transform import transform_text


def _remaining_originals(text: str, spans: list[Span]) -> tuple[str, ...]:
    """Check whether exact original detected values appear after transformation.

    This does NOT assess indirect identification or information that is
    recoverable through external knowledge.
    """
    leaked = []
    for span in spans:
        # Use word boundaries for word-like values; no false substring matches.
        if re.search(r"(?<!\w)" + re.escape(span.text) + r"(?!\w)", text, re.IGNORECASE):
            leaked.append(span.text)
    return tuple(leaked)


def run_pipeline(
    text: str,
    *,
    language: str = "de",
    strategies: Mapping[str, str] | None = None,
    shift_days: int = 30,
    detector: RegexDetector | None = None,
) -> PipelineResult:
    engine = detector or RegexDetector()
    found = engine.detect(text, language=language)
    output = transform_text(text, found, strategies, language=language, shift_days=shift_days)
    return PipelineResult(text, output, tuple(found), _remaining_originals(output, found))


def audit_external_text(text: str, *, language: str = "de") -> list[Span]:
    """Flag possible identifiers in externally transformed text.

    A rule match is a review flag, not proof that a real patient's identity
    remains exposed. No original available means no leakage denominator.
    """
    return RegexDetector().detect(text, language=language)
