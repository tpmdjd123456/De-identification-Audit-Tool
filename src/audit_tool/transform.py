"""Configurable, reproducible transformations by identifier type."""
from datetime import datetime, timedelta
from hashlib import sha256
import re
from typing import Mapping, Sequence
from .models import Span

_STRATEGIES = {"placeholder", "mask", "keep", "surrogate", "date_shift", "generalize"}
_SURROGATES = {
    "PERSON": ["Mara Beispiel", "Lena Muster", "Jonas Beispiel", "Klara Muster", "Alex Sample"],
    "LOCATION": ["Hamburg", "Leipzig", "Dresden", "Berlin", "Bremen"],
}


def _surrogate(span: Span, seed: str) -> str:
    options = _SURROGATES.get(span.label)
    if not options:
        return f"[{span.label}]"
    digest = sha256(f"{seed}|{span.label}|{span.text.casefold()}".encode("utf-8")).digest()
    start = int.from_bytes(digest[:4], "big") % len(options)
    for step in range(len(options)):
        value = options[(start + step) % len(options)]
        if value.casefold() != span.text.casefold():
            return value
    return f"[{span.label}]"


def _shift_date(value: str, days: int) -> str:
    fmt = "%Y-%m-%d" if "-" in value else "%d.%m.%Y" if "." in value else "%d/%m/%Y"
    try:
        return (datetime.strptime(value, fmt) + timedelta(days=days)).strftime(fmt)
    except (ValueError, OverflowError):
        return "[DATE]"


def _generalize(span: Span, language: str) -> str:
    if span.label == "AGE":
        numbers = re.search(r"\d{1,3}", span.text)
        if numbers:
            age = int(numbers.group())
            if age <= 120:
                low = (age // 10) * 10
                return f"{low}–{low + 9} " + ("Jahre" if language == "de" else "years")
    return f"[{span.label}]"


def transform_text(
    text: str,
    spans: Sequence[Span],
    strategies: Mapping[str, str] | None = None,
    *,
    language: str = "de",
    shift_days: int = 30,
    surrogate_seed: str = "demo-only",
) -> str:
    """Apply type-dependent transforms, preserving non-identifier text exactly.

    `surrogate_seed` is a reproducibility control, not an encryption key.
    Do not consider deterministic surrogates a security guarantee.
    """
    if language not in {"de", "en"}:
        raise ValueError("Language must be de or en")
    choices = dict(strategies or {})
    if any(strategy not in _STRATEGIES for strategy in choices.values()):
        raise ValueError(f"Valid strategies: {sorted(_STRATEGIES)}")
    result: list[str] = []
    cursor = 0
    for span in sorted(spans, key=lambda s: s.start):
        if span.start < cursor or span.end > len(text) or text[span.start:span.end] != span.text:
            raise ValueError("Overlapping or invalid detector spans")
        result.append(text[cursor:span.start])
        strategy = choices.get(span.label, "placeholder")
        if strategy == "keep":
            replacement = span.text
        elif strategy == "mask":
            replacement = "*" * len(span.text)
        elif strategy == "surrogate":
            replacement = _surrogate(span, surrogate_seed)
        elif strategy == "date_shift" and span.label == "DATE":
            replacement = _shift_date(span.text, shift_days)
        elif strategy == "generalize":
            replacement = _generalize(span, language)
        else:
            replacement = f"[{span.label}]"
        result.append(replacement)
        cursor = span.end
    result.append(text[cursor:])
    return "".join(result)
