"""Regression tests for the reviewed Issue #18 integration (2026-11-15).

These are synthetic examples; they assert replacement mechanics, not anonymity.
"""
from pathlib import Path
import re

import pytest

from audit_tool import (
    RegexDetector,
    audit_external_text,
    run_pipeline,
    transform_text,
    span_from_entity,
    spans_from_entities,
    transform_entities,
)
from audit_tool.categories import classify, unknown_labels
from audit_tool.config import TransformConfig, standard_pipelines
from audit_tool.models import Span
from audit_tool.transform import transform_document, document_date_offset
from evaluation.grascco_io import load_documents


def s(text, value, label, occurrence=0):
    start = 0
    for i in range(occurrence + 1):
        start = text.index(value, start)
        if i < occurrence:
            start += len(value)
    return Span(start, start + len(value), label, value)


P2 = standard_pipelines("integration-test")[2]


def test_separate_location_subtypes_from_titles_and_ids():
    cases = {
        "LOCATION_STREET": "street", "LOCATION_ZIP": "zip",
        "LOCATION_CITY": "place", "LOCATION_HOSPITAL": "hospital",
        "LOCATION_ORGANIZATION": "employer", "NAME_TITLE": "title",
        "NAME_USERNAME": "id", "NAME_DOCTOR": "person",
    }
    assert {k: classify(k) for k in cases} == cases
    assert unknown_labels([*cases, "UNKNOWN_NEW_LABEL"]) == ["UNKNOWN_NEW_LABEL"]


def test_ids_preserve_shape_and_never_survive_verbatim():
    note = "Fall-Nr. AB-4471; nochmal AB-4471."
    spans = [s(note, "AB-4471", "ID"), s(note, "AB-4471", "ID", 1)]
    result = transform_document(note, spans, document_id="id_doc", config=P2)
    a, b = (r.replacement for r in result.records)
    assert a == b
    assert a != "AB-4471"
    assert re.fullmatch(r"[A-Z]{2}-\d{4}", a)
    assert result.output_text.count(a) == 2


def test_telephone_fax_preserve_separators_and_email_uses_reserved_domain():
    note = "Tel 030/123-456, Fax 040-123/99. Kontakt test@somewhere.de."
    spans = [s(note, "030/123-456", "CONTACT_PHONE"),
             s(note, "040-123/99", "CONTACT_FAX"),
             s(note, "test@somewhere.de", "CONTACT_EMAIL")]
    result = transform_document(note, spans, document_id="contacts", config=P2)
    phone, fax, email = (r.replacement for r in result.records)
    assert re.fullmatch(r"\d{3}/\d{3}-\d{3}", phone)
    assert re.fullmatch(r"\d{3}-\d{3}/\d{2}", fax)
    assert email.endswith("@example.invalid")
    assert all(row.replacement != row.original for row in result.records)


def test_mask_default_cannot_reveal_identifier_length():
    note = "Anna Müller und A. B."
    spans = [s(note, "Anna Müller", "NAME_PATIENT"), s(note, "A. B.", "NAME_RELATIVE")]
    result = transform_document(note, spans, document_id="mask", config=standard_pipelines()[0])
    assert [row.replacement for row in result.records] == ["[MASKED]", "[MASKED]"]
    char_config = TransformConfig(name="characters", mask_style="characters", per_category={"person": "mask"})
    character = transform_document(note, spans, document_id="mask", config=char_config)
    assert len(character.records[0].replacement) == len("Anna Müller")
    assert len(character.records[1].replacement) == len("A. B.")


def test_city_street_postcode_hospital_have_different_policies():
    note = "Berlin, Musterstraße 12, PLZ 10115, Klinik Erfurt."
    spans = [s(note, "Berlin", "LOCATION_CITY"),
             s(note, "Musterstraße 12", "LOCATION_STREET"),
             s(note, "10115", "LOCATION_ZIP"),
             s(note, "Klinik Erfurt", "LOCATION_HOSPITAL")]
    result = transform_document(note, spans, document_id="location", config=P2)
    assert [r.category for r in result.records] == ["place", "street", "zip", "hospital"]
    assert [r.replacement for r in result.records] == ["Deutschland", "[STREET]", "[ZIP]", "medizinische Einrichtung"]


def test_detector_adapter_uses_existing_source_offsets():
    text = "Patientin Anna Müller wurde untersucht."
    start, end = text.index("Anna Müller"), text.index("Anna Müller") + len("Anna Müller")
    entity = {"start": start, "end": end, "type": "NAME_PATIENT"}
    span = span_from_entity(entity, text, source="presidio")
    assert span.source == "presidio" and span.text == "Anna Müller"
    result = transform_entities(text, [entity], document_id="adapters", config=P2, source="presidio")
    assert len(result.records) == 1
    assert result.records[0].label == "NAME_PATIENT"
    assert "Anna Müller" not in result.output_text
    with pytest.raises(ValueError, match="Invalid entity offsets"):
        spans_from_entities([{"start": 0, "end": 100, "type": "PERSON"}], text)
    with pytest.raises(ValueError, match="does not match"):
        span_from_entity({"start": start, "end": end, "type": "PERSON", "text": "wrong"}, text)
    with pytest.raises(ValueError, match="Overlapping"):
        transform_entities(text, [entity, entity], document_id="overlap", config=P2)


def test_year_only_and_named_month_year_never_pass_through_unchanged():
    note = "In 2006 und Dezember 2016."
    spans = [s(note, "2006", "DATE"), s(note, "Dezember 2016", "DATE")]
    result = transform_document(note, spans, document_id="partial_date", config=P2)
    assert all(r.replacement != r.original for r in result.records)
    assert all(r.replacement.startswith("[") or r.category == "date" for r in result.records)


def test_explicit_zero_risk_of_identical_direct_replacement_across_seeds():
    note = "Patientin Anna Müller; Fall-ID A1-12"
    spans = [s(note, "Anna Müller", "NAME_PATIENT"), s(note, "A1-12", "ID")]
    for seed in ("a", "b", "a third longer seed"):
        result = transform_document(note, spans, document_id="seed-test", config=standard_pipelines(seed)[2])
        assert all(r.replacement != r.original for r in result.records)


def test_missing_kind_is_redacted_not_skipped_and_eponym_name_safe():
    note = "Name: Alzheimer; marker: X23."
    spans = [s(note, "Alzheimer", "NAME_RELATIVE"), s(note, "X23", "")]
    result = transform_document(note, spans, document_id="unknown", config=P2)
    assert result.records[0].replacement != "Alzheimer"
    assert result.records[1].replacement == "[UNKNOWN]"
    assert len(result.records) == 2


def test_config_roundtrip_preserves_new_mask_policy():
    original = TransformConfig(name="custom", mask_style="characters", mask_token="[REDACTED]", per_category={"hospital": "placeholder"})
    assert TransformConfig.from_json(original.to_json()) == original


def test_legacy_demo_api_remains_compatible():
    assert RegexDetector() is not None
    note = "Patient Anna Müller war in Berlin am 12.10.2026."
    outcome = run_pipeline(note, language="de")
    assert "[PERSON]" in outcome.transformed_text
    assert transform_text(note, outcome.spans) == outcome.transformed_text
    assert isinstance(audit_external_text("Patient John Smith", language="en"), list)


CORPUS = Path(__file__).resolve().parents[1] / "data/grascco/grascco_phi_annotation_json.zip"


@pytest.mark.skipif(not CORPUS.exists(), reason="German GraSCCo_PHI archive not present")
def test_real_corpus_all_three_configs_replace_every_non_keep_span():
    docs = load_documents(CORPUS)
    assert len(docs) == 63
    assert sum(len(d.spans) for d in docs) == 1439
    for config in standard_pipelines()[:3]:
        for doc in docs:
            result = transform_document(doc.text, doc.spans, document_id=doc.document_id, config=config)
            assert len(result.records) == len(doc.spans)
            assert all(r.original != r.replacement for r in result.records)
