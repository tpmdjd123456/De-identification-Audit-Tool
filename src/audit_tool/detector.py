"""Transparent baseline rules, intentionally NOT a production-grade PHI detector."""
import re
from .models import Span


class RegexDetector:
    """Small bilingual baseline that can be replaced by Presidio or NER models.

    Names need a title/role prefix. City names are a SHORT demo dictionary.
    It will miss identifiers and may produce false positives; evaluate with
    annotated documents before making any comparative research claims.
    """

    _NAME = re.compile(
        r"\b(?i:patient|patientin|frau|herr|mr|mrs|ms)\s*:?\s+"
        r"(?P<value>[A-ZÄÖÜ][a-zäöüß]+(?:[-'][A-ZÄÖÜ][a-zäöüß]+)?"
        r"(?:\s+[A-ZÄÖÜ][a-zäöüß]+(?:[-'][A-ZÄÖÜ][a-zäöüß]+)?){1,2})\b"
    )
    _DATE = re.compile(
        r"\b(?:\d{1,2}[./]\d{1,2}[./](?:19|20)\d{2}|"
        r"(?:19|20)\d{2}-\d{2}-\d{2})\b"
    )
    _PATIENT_ID = re.compile(
        r"\b(?i:patient[- ]?id|patienten[- ]?id|patientennummer|mrn)"
        r"\s*[:#]?\s*(?P<value>[A-Za-z0-9][A-Za-z0-9-]{3,30})\b"
    )
    _LOCATION = re.compile(
        r"\b(?i:in|aus|from|wohnhaft\s+in)\s+"
        r"(?P<value>(?i:Berlin|Hamburg|München|Munich|Köln|Cologne|Leipzig|"
        r"Dresden|Frankfurt|Bremen|London|Oxford))\b"
    )
    _AGE = re.compile(
        r"\b(?P<value>\d{1,3}\s*(?i:Jahre\s+alt|Jahre|years\s+old|year-old))\b"
    )

    def detect(self, text: str, language: str = "de") -> list[Span]:
        if language not in {"de", "en"}:
            raise ValueError("Language must be 'de' or 'en'")
        found: list[Span] = []
        for label, rule in (
            ("PATIENT_ID", self._PATIENT_ID),
            ("PERSON", self._NAME),
            ("DATE", self._DATE),
            ("LOCATION", self._LOCATION),
            ("AGE", self._AGE),
        ):
            for match in rule.finditer(text):
                a, b = match.span("value") if "value" in match.re.groupindex else match.span()
                found.append(Span(a, b, label, text[a:b]))

        # Choose a stable non-overlapping set of spans, so text substitution is safe.
        found.sort(key=lambda s: (s.start, -(s.end - s.start), s.label))
        result: list[Span] = []
        for span in found:
            if not result or span.start >= result[-1].end:
                result.append(span)
        return result
