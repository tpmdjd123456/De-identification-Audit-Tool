"""Issue #18: unit + corpus-dependent transformation regression tests."""
from dataclasses import asdict
from datetime import datetime
from pathlib import Path
import json
import pytest

from audit_tool.categories import classify, unknown_labels
from audit_tool.config import standard_pipelines, TransformConfig
from audit_tool.models import Span
from audit_tool.transform import document_date_offset, transform_document
from evaluation.grascco_io import load_documents, parse_json
from evaluation.inventory_labels import build_inventory

P2 = standard_pipelines("fixed-seed")[2]


def span(text: str, value: str, label: str = "NAME_PATIENT", start: int = 0) -> Span:
    found = text.index(value, start)
    return Span(found, found + len(value), label, value)


def test_unknown_label_fails_closed():
    text = "geheim XYZ"
    result = transform_document(text, [span(text, "XYZ", "NEW_UNSEEN_LABEL")], document_id="x", config=P2)
    assert result.output_text == "geheim [UNKNOWN]"
    assert result.records[0].category == "unknown"


def test_length_changes_do_not_corrupt_following_offsets():
    text = "x Anna Müller y 2010-04-05 z"
    spans = [span(text, "Anna Müller"), span(text, "2010-04-05", "DATE")]
    shorter = transform_document(text, spans, document_id="short", config=standard_pipelines()[1])
    longer = transform_document(text, spans, document_id="long", config=P2)
    assert "[PERSON]" in shorter.output_text and " z" in shorter.output_text
    assert "A. Beispiel" in longer.output_text or "B. Muster" in longer.output_text or "C. Beispiel" in longer.output_text or "D. Muster" in longer.output_text
    assert "2010-04-05" not in longer.output_text
    assert longer.output_text.endswith(" z")


def test_overlapping_span_rejected():
    text = "Anna Müller"
    with pytest.raises(ValueError, match="Overlapping spans"):
        transform_document(text, [Span(0, 4, "NAME_PATIENT", "Anna"),
                                  Span(2, 10, "NAME_DOCTOR", "na Müller")], document_id="x", config=P2)


def test_wrong_offset_rejected():
    with pytest.raises(ValueError, match="does not match"):
        transform_document("Hallo", [Span(0, 5, "NAME_PATIENT", "other")], document_id="x", config=P2)


def test_same_seed_same_output_different_seed_changes():
    text = "Patientin Anna Müller am 12.10.2026."
    spans = [span(text, "Anna Müller"), span(text, "12.10.2026", "DATE")]
    a = transform_document(text, spans, document_id="abc", config=standard_pipelines("one")[2])
    b = transform_document(text, spans, document_id="abc", config=standard_pipelines("one")[2])
    c = transform_document(text, spans, document_id="abc", config=standard_pipelines("different")[2])
    assert a == b
    assert a.output_text != c.output_text


def test_same_person_surname_alias_consistency():
    text = "Patientin Anna Müller kam. Müller wurde untersucht."
    spans = [span(text, "Anna Müller"), span(text, "Müller", start=21)]
    output = transform_document(text, spans, document_id="x", config=P2)
    assert output.records[0].replacement == output.records[1].replacement
    assert output.records[0].replacement.startswith(("Lena", "Mara", "Alina", "Klara"))


def test_date_intervals_preserved_and_documents_get_different_offsets():
    text = "Am 01.02.2024 kam sie und am 04.02.2024 ging sie."
    spans = [span(text, "01.02.2024", "DATE"), span(text, "04.02.2024", "DATE")]
    a = transform_document(text, spans, document_id="patient_a", config=P2)
    b = transform_document(text, spans, document_id="patient_b", config=P2)
    assert a.date_offset_days != b.date_offset_days
    original_delta = datetime.strptime(spans[1].text, "%d.%m.%Y") - datetime.strptime(spans[0].text, "%d.%m.%Y")
    shifted_delta = (datetime.strptime(a.records[1].replacement, "%d.%m.%Y") -
                     datetime.strptime(a.records[0].replacement, "%d.%m.%Y"))
    assert original_delta == shifted_delta


def test_all_supported_date_forms_and_unparseable():
    values = ("01.02.2024", "1.2.2024", "2024-02-01", "2024", "02/2024", "21.")
    text = ", ".join(values)
    spans = []
    pos = 0
    for value in values:
        found = text.index(value, pos)
        spans.append(Span(found, found + len(value), "DATE", value))
        pos = found + len(value)
    result = transform_document(text, spans, document_id="dates", config=P2)
    assert result.records[-1].replacement == "[DATE]"
    assert all(row.replacement != row.original for row in result.records)
    assert result.records[2].replacement.count("-") == 2
    assert len(result.records[3].replacement) == 4
    assert "/" in result.records[4].replacement


def test_age_is_five_year_band_and_original_is_not_preserved():
    text = "49 Jahre alt"
    result = transform_document(text, [span(text, "49", "AGE")], document_id="age", config=P2)
    assert result.output_text == "45–49 Jahre alt"
    assert result.records[0].replacement != "49"


def test_config_json_round_trip_and_keep():
    restored = TransformConfig.from_json(P2.to_json())
    assert restored == P2
    config = TransformConfig(name="keep", per_category={"place": "keep"})
    text = "Berlin"
    result = transform_document(text, [span(text, text, "LOCATION_CITY")], document_id="a", config=config)
    assert result.output_text == "Berlin"


def test_region_and_sector_fallbacks_are_recorded():
    text = "Berlin. Unbekanntstadt. Floristin."
    spans = [span(text, "Berlin", "LOCATION_CITY"),
             span(text, "Unbekanntstadt", "LOCATION_CITY"),
             span(text, "Floristin", "PROFESSION")]
    result = transform_document(text, spans, document_id="x", config=P2)
    assert result.records[0].replacement == "Deutschland"  # City-states need a coarser level.
    assert result.records[1].replacement == "[REGION]"
    assert result.records[1].fallback_reason
    assert result.records[2].replacement == "Einzelhandel und Dienstleistungen"


def test_utf16_offsets_conversion():
    src = "a😀b Anna"
    fixture = {"%FEATURE_STRUCTURES": [
        {"%TYPE": "uima.cas.Sofa", "sofaString": src},
        {"%TYPE": "webanno.custom.PHI", "begin": 5, "end": 9, "kind": "NAME_PATIENT"}]}
    document = parse_json(fixture, "emoji")
    assert document.spans[0].text == "Anna"


CORPUS = Path(__file__).parents[1] / "data/grascco/grascco_phi_annotation_json.zip"


@pytest.mark.skipif(not CORPUS.exists(), reason="GraSCCo_PHI corpus not present locally")
def test_real_grascco_document_and_inventory():
    docs = load_documents(CORPUS)
    assert len(docs) == 63
    inventory = build_inventory(docs)
    assert inventory["annotations"] == 1439
    assert inventory["unmapped_labels"] == []
    assert sum(row["label"] == "<MISSING>" for row in inventory["labels"]) == 1
    doc = docs[0]
    result = transform_document(doc.text, doc.spans, document_id=doc.document_id, config=P2)
    assert len(result.records) == len(doc.spans)
    for row in result.records:
        if row.strategy != "keep":
            assert row.replacement != row.original
