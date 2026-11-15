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


# Issue #18: corpus-validated, independently callable transformation layer.
from dataclasses import asdict
from .categories import classify
from .config import TransformConfig, CATEGORY_STRATEGIES
from .models import DocumentTransformation, TransformationRecord

_PERSON_NAMES = {
    "female": ("Lena Beispiel", "Mara Muster", "Alina Beispiel", "Klara Muster"),
    "male": ("Jonas Beispiel", "Paul Muster", "Leon Beispiel", "Felix Muster"),
    "unknown": ("A. Beispiel", "B. Muster", "C. Beispiel", "D. Muster"),
}
# Intentionally small, auditable, conservative mapping. Unknown places fail closed.
_REGIONS = {
    "berlin": "Berlin", "hamburg": "Hamburg", "bremen": "Bremen",
    "münchen": "Bayern", "munich": "Bayern", "augsburg": "Bayern", "nürnberg": "Bayern",
    "leipzig": "Sachsen", "dresden": "Sachsen", "chemnitz": "Sachsen",
    "köln": "Nordrhein-Westfalen", "düsseldorf": "Nordrhein-Westfalen",
    "bonn": "Nordrhein-Westfalen", "dortmund": "Nordrhein-Westfalen",
    "frankfurt": "Hessen", "wiesbaden": "Hessen", "kassel": "Hessen",
    "hannover": "Niedersachsen", "göttingen": "Niedersachsen",
    "stuttgart": "Baden-Württemberg", "heidelberg": "Baden-Württemberg",
    "freiburg": "Baden-Württemberg", "mannheim": "Baden-Württemberg",
    "rostock": "Mecklenburg-Vorpommern", "kiel": "Schleswig-Holstein",
    "lübeck": "Schleswig-Holstein", "mainz": "Rheinland-Pfalz",
    "erfurt": "Thüringen", "jena": "Thüringen", "magdeburg": "Sachsen-Anhalt",
    "saarbrücken": "Saarland", "klagenfurt": "Kärnten", "graz": "Steiermark",
    "wien": "Wien", "salzburg": "Salzburg",
    "usa": "Nordamerika", "peru": "Südamerika",
}
_PROFESSION_SECTORS = {
    "floristin": "Einzelhandel und Dienstleistungen",
    "florist": "Einzelhandel und Dienstleistungen",
    "maschinenbauingenieur": "Ingenieurwesen und Technik",
    "maschinenbauingenieurin": "Ingenieurwesen und Technik",
    "pfleger": "Gesundheitswesen", "pflegerin": "Gesundheitswesen",
    "arzt": "Gesundheitswesen", "ärztin": "Gesundheitswesen",
    "monteur": "Handwerk und Technik", "monteurin": "Handwerk und Technik",
    "verkäufer": "Einzelhandel und Dienstleistungen", "verkäuferin": "Einzelhandel und Dienstleistungen",
}


def _stable_hash(*pieces: str) -> bytes:
    return sha256("|".join(pieces).encode("utf-8")).digest()


def document_date_offset(document_id: str, config: TransformConfig) -> int:
    """Stable document-specific offset; not cryptographic anonymization."""
    digest = _stable_hash(config.seed, document_id, "document-date-offset")
    width = config.date_shift_max_days - config.date_shift_min_days + 1
    days = config.date_shift_min_days + int.from_bytes(digest[:8], "big") % width
    return days if digest[-1] & 1 else -days


def _shift_date_robust(original: str, offset_days: int) -> tuple[str, str | None]:
    """Preserve date notation; uncertain partial day-only annotations fail closed.

    Bare years and month/year lack complete event dates. Anchor them at mid-year
    or mid-month to apply the same document offset; interval checks apply only
    to fully specified dates.
    """
    value = original.strip()
    for fmt in ("%d.%m.%Y", "%d.%m.%y", "%d/%m/%Y", "%d/%m/%y", "%Y-%m-%d", "%d-%m-%Y", "%d-%m-%y"):
        try:
            dt = datetime.strptime(value, fmt)
            if dt.strftime(fmt) != value and not (fmt.startswith("%d.") and dt.strftime(fmt).lstrip("0") == value):
                # Do not silently normalize a partial or ambiguous formatting pattern.
                # For single-digit day/month, strptime still accepts input; formatted
                # output below restores the original component widths.
                pass
            shifted = dt + timedelta(days=offset_days)
            if fmt.startswith("%Y-"):
                return shifted.strftime(fmt), None
            separator = "." if "." in value else "/" if "/" in value else "-"
            parts = value.split(separator)
            year_digits = len(parts[2])
            y = shifted.strftime("%y" if year_digits == 2 else "%Y")
            d = str(shifted.day).zfill(len(parts[0]))
            m = str(shifted.month).zfill(len(parts[1]))
            return separator.join([d, m, y]), None
        except (ValueError, OverflowError):
            continue
    month_year = re.fullmatch(r"(0?[1-9]|1[0-2])([./])((?:19|20)\d{2}|\d{2})", value)
    if month_year:
        month, sep, year = month_year.groups()
        year_full = int(year) if len(year) == 4 else (2000 + int(year) if int(year) <= 68 else 1900 + int(year))
        try:
            dt = datetime(year_full, int(month), 15) + timedelta(days=offset_days)
            return f"{str(dt.month).zfill(len(month))}{sep}{str(dt.year)[-len(year):]}", "partial-month-year"
        except (ValueError, OverflowError):
            pass
    if re.fullmatch(r"(?:19|20)\d{2}", value):
        try:
            dt = datetime(int(value), 7, 1) + timedelta(days=offset_days)
            return str(dt.year), "partial-year"
        except (ValueError, OverflowError):
            pass
    # German month names and common abbreviations in clinical letters.
    month_forms = (
        ("januar", "jan"), ("februar", "feb"), ("märz", "mär", "maerz", "mrz"),
        ("april", "apr"), ("mai",), ("juni", "jun"), ("juli", "jul"),
        ("august", "aug"), ("september", "sept", "sep"),
        ("oktober", "okt"), ("november", "nov"), ("dezember", "dez"),
    )
    def resolve_month(word):
        cleaned = word.casefold().rstrip(".")
        for number, forms in enumerate(month_forms, 1):
            if cleaned in forms:
                return number
        return None
    def month_like(number, original_month):
        # Keep the language, capitalization and abbreviation style.
        names = ("Januar", "Februar", "März", "April", "Mai", "Juni", "Juli",
                 "August", "September", "Oktober", "November", "Dezember")
        source = original_month.rstrip(".")
        answer = names[number - 1]
        if len(source) <= 4:
            answer = answer[:len(source)]
        if source.islower():
            answer = answer.lower()
        if original_month.endswith("."):
            answer += "."
        return answer
    named = re.fullmatch(
        r"(?:(?P<day>\d{1,2})(?P<between>\.\s*))?"
        r"(?P<month>[A-Za-zÄÖÜäöü]+\.?)(?P<space>\s*)"
        r"(?P<year>(?:19|20)\d{2}|\d{2})", value)
    if named:
        month = resolve_month(named.group("month"))
        if month:
            year = named.group("year")
            full_year = int(year) if len(year) == 4 else (2000 + int(year) if int(year) <= 68 else 1900 + int(year))
            day = int(named.group("day")) if named.group("day") else 15
            try:
                shifted = datetime(full_year, month, day) + timedelta(days=offset_days)
                month_text = month_like(shifted.month, named.group("month"))
                output_year = str(shifted.year)[-len(year):]
                if named.group("day"):
                    return (str(shifted.day).zfill(len(named.group("day"))) + named.group("between")
                            + month_text + named.group("space") + output_year), None
                return month_text + named.group("space") + output_year, "partial-month-year"
            except (ValueError, OverflowError):
                pass
    # Full numeric dates with extra spaces that strptime does not accept.
    spaced = re.fullmatch(r"(\d{1,2})([.\-/]\s*|\s+)(\d{1,2})([.\-/]\s*|\s+)(\d{2}|\d{4})", value)
    if spaced:
        day, sep1, month, sep2, year = spaced.groups()
        full_year = int(year) if len(year) == 4 else (2000 + int(year) if int(year) <= 68 else 1900 + int(year))
        try:
            shifted = datetime(full_year, int(month), int(day)) + timedelta(days=offset_days)
            return (str(shifted.day).zfill(len(day)) + sep1 + str(shifted.month).zfill(len(month))
                    + sep2 + str(shifted.year)[-len(year):]), None
        except (ValueError, OverflowError):
            pass
    return "[DATE]", "unparseable-date"


def _person_gender(text: str, span: Span) -> str:
    prefix = text[max(0, span.start - 90):span.start].casefold()
    if re.search(r"(?:\bpatientin\b|\bfrau\b|\bärztin\b|\bschwester\b)\W*$", prefix):
        return "female"
    if re.search(r"(?:\bherr\b|\bpatient\b|\barzt\b)\W*$", prefix):
        return "male"
    return "unknown"  # initial rather than an unjustified gender assumption


def _alias_keys(spans: Sequence[Span]) -> dict[tuple[str, str], str]:
    """Resolve unambiguous surname-only repeats to the same full-name key."""
    from collections import defaultdict
    whole = defaultdict(set)
    for s in spans:
        if classify(s.label) != "person":
            continue
        normalized = re.sub(r"\s+", " ", s.text.strip()).casefold()
        if len(normalized.split()) > 1:
            whole[(s.label, normalized.split()[-1])].add(normalized)
    result = {}
    for (label, surname), choices in whole.items():
        if len(choices) == 1:
            result[(label, surname)] = next(iter(choices))
    return result


def _generalize_location(original: str, label: str) -> tuple[str, str | None]:
    value = re.sub(r"\s+", " ", original.strip()).casefold()
    # Country -> continent; otherwise matched city -> state/region.
    if value in _REGIONS:
        region = _REGIONS[value]
        if value in {"berlin", "bremen", "hamburg"}:
            return "Deutschland", None  # otherwise no generalization occurs
        return region, None
    if label == "LOCATION_HOSPITAL":
        matches = {region for name, region in _REGIONS.items()
                   if re.search(r"(?<!\w)" + re.escape(name) + r"(?!\w)", value)}
        if len(matches) == 1:
            return next(iter(matches)), None
    return "[REGION]", "unmapped-geographic-hierarchy"


def _generalize_profession(original: str) -> tuple[str, str | None]:
    value = re.sub(r"\s+", " ", original.strip()).casefold()
    if value in _PROFESSION_SECTORS:
        return _PROFESSION_SECTORS[value], None
    # Accept common German inflected endings only if a unique known stem matches.
    possible = {sector for occupation, sector in _PROFESSION_SECTORS.items()
                if value in (occupation + "s", occupation + "n", occupation + "en", occupation + "innen")}
    if len(possible) == 1:
        return next(iter(possible)), None
    return "[PROFESSION]", "unmapped-profession-sector"


def _consistent_surrogate(span: Span, text: str, document_id: str, seed: str,
                          aliases: dict, gender_cache: dict) -> str:
    label = span.label or "UNKNOWN"
    normalized = re.sub(r"\s+", " ", span.text.strip()).casefold()
    if classify(label) == "person":
        person_key = aliases.get((label, normalized), normalized)
        # Gender is selected from any full-name occurrence when possible, rather
        # than from a later abbreviated mention lacking context.
        gender = gender_cache.get((label, person_key), "unknown")
        options = _PERSON_NAMES[gender]
        index = int.from_bytes(_stable_hash(seed, document_id, label, person_key)[:8], "big") % len(options)
        candidate = options[index]
        if candidate.casefold() == normalized:
            return "[PERSON]"
        return candidate
    digest = _stable_hash(seed, document_id, label, normalized).hex()[:12]
    if label == "CONTACT_EMAIL":
        return f"kontakt-{digest}@example.invalid"
    if label in ("CONTACT_PHONE", "CONTACT_FAX"):
        return f"KONTAKT-{digest}"
    if label == "NAME_USERNAME":
        return f"user-{digest}"
    if classify(label) == "id":
        return f"ID-{digest}"
    return f"[{label or 'UNKNOWN'}]"


def transform_document(text: str, spans: Sequence[Span], *, document_id: str,
                       config: TransformConfig) -> DocumentTransformation:
    """Apply one reproducible policy using verified, non-overlapping offsets.

    Gold annotations / detector spans are unchanged. Every span produces a
    record with strategy, original, replacement and any conservative fallback.
    This layer does not itself assess de-identification safety.
    """
    if not document_id:
        raise ValueError("document_id is required")
    ordered = sorted(spans, key=lambda s: (s.start, s.end))
    cursor = 0
    for span in ordered:
        if span.start < cursor:
            raise ValueError(f"Overlapping spans at offset {span.start} in {document_id}")
        if span.end > len(text) or text[span.start:span.end] != span.text:
            raise ValueError(f"Span does not match document at {span.start}:{span.end} in {document_id}")
        cursor = span.end
    offset = document_date_offset(document_id, config)
    aliases = _alias_keys(ordered)
    gender_cache = {}
    for span in ordered:
        if classify(span.label) != "person":
            continue
        normalized = re.sub(r"\s+", " ", span.text.strip()).casefold()
        person_key = aliases.get((span.label, normalized), normalized)
        gender = _person_gender(text, span)
        if gender != "unknown":
            gender_cache[(span.label, person_key)] = gender
    output = []
    rows = []
    cursor = 0
    for span in ordered:
        category = classify(span.label)
        strategy = config.per_category.get(category, "placeholder")
        original = span.text
        fallback = None
        if strategy == "keep":
            replacement = original
        elif strategy == "mask":
            replacement = "█" * len(original)
        elif strategy == "placeholder":
            replacement = f"[{category.upper()}]" if category != "unknown" else "[UNKNOWN]"
        elif strategy == "surrogate":
            if category in ("person", "contact", "id"):
                replacement = _consistent_surrogate(span, text, document_id, config.seed, aliases, gender_cache)
            else:
                replacement, fallback = f"[{category.upper()}]", "unsupported-surrogate-category"
        elif strategy == "date_shift":
            if category == "date":
                replacement, fallback = _shift_date_robust(original, offset)
            else:
                replacement, fallback = f"[{category.upper()}]", "date-shift-on-non-date"
        elif strategy == "generalize":
            if category == "age":
                if re.fullmatch(r"\d{1,3}", original.strip()) and 0 <= int(original.strip()) <= 120:
                    age = int(original.strip())
                    low = (age // config.age_band_width) * config.age_band_width
                    replacement = f"{low}–{low + config.age_band_width - 1}"
                else:
                    replacement, fallback = "[AGE]", "unparseable-age"
            elif category in ("place", "employer"):
                replacement, fallback = _generalize_location(original, span.label)
            elif category == "profession":
                replacement, fallback = _generalize_profession(original)
            else:
                replacement, fallback = f"[{category.upper()}]", "unsupported-generalization-category"
        else:
            raise ValueError(f"Unknown strategy {strategy}")
        # Nothing may be silently kept because the dictionary failed.
        output.extend((text[cursor:span.start], replacement))
        rows.append(TransformationRecord(span.label or "<MISSING>", category, strategy,
                                         original, replacement, span.start, span.end, fallback))
        cursor = span.end
    output.append(text[cursor:])
    return DocumentTransformation(document_id, "".join(output), config.to_dict(), tuple(rows), offset)
