"""Regressions for the GraSCCo Streamlit review workflow, independent of Streamlit."""
import json
from pathlib import Path
import pytest

from audit_tool.models import Span
from evaluation.document_review import DEFAULT_ARCHIVE, PIPELINE_NAMES, review_document, load_review_documents
from evaluation.grascco_io import GraSCCoDocument


def test_three_compare_pipelines_have_stable_names():
    assert PIPELINE_NAMES == ("P0_mask", "P1_placeholder", "P2_surrogate")


def test_review_shows_original_and_logs_actual_replacements():
    source = "Patientin Anna Müller, 67 Jahre, in Leipzig, am 12.10.2026."
    def target(value, label):
        i = source.index(value)
        return Span(i, i + len(value), label, value)
    document = GraSCCoDocument(
        "synthetic-1", source,
        (target("Anna Müller", "NAME_PATIENT"), target("67", "AGE"),
         target("Leipzig", "LOCATION_CITY"), target("12.10.2026", "DATE")),
    )
    outcomes = {name: review_document(document, name) for name in PIPELINE_NAMES}
    for name, result in outcomes.items():
        assert result.document.text == source
        assert result.unchanged_count == 0
        assert result.original_string_flags == 0
        assert len(result.audit_rows()) == len(document.spans)
        assert all(row["original"] != row["replacement"] for row in result.audit_rows())
        assert json.dumps(result.audit_rows(), ensure_ascii=False)
        assert result.transformation.config["name"] == name
    assert "[MASKED]" in outcomes["P0_mask"].transformation.output_text
    assert "[PERSON]" in outcomes["P1_placeholder"].transformation.output_text
    assert "65–69" in outcomes["P2_surrogate"].transformation.output_text
    assert "Sachsen" in outcomes["P2_surrogate"].transformation.output_text
    assert "12.10.2026" not in outcomes["P2_surrogate"].transformation.output_text


def test_reappearance_flags_not_confused_with_unchanged_span():
    text = "Patient Anna Müller hatte einen Termin. Anna Müller kam erneut."
    begin = text.index("Anna Müller")
    doc = GraSCCoDocument("repeat", text, (Span(begin, begin + 11, "NAME_PATIENT", "Anna Müller"),))
    review = review_document(doc, "P1_placeholder")
    assert review.unchanged_count == 0
    assert review.original_string_flags == 1


def test_unrecognized_comparison_pipeline_rejected():
    document = GraSCCoDocument("empty", "No identifiers", ())
    with pytest.raises(ValueError, match="Unknown comparison pipeline"):
        review_document(document, "P3_keep_quasi")


@pytest.mark.skipif(not DEFAULT_ARCHIVE.is_file(), reason="GraSCCo_PHI ZIP unavailable")
def test_real_german_corpus_review_workflow():
    documents = load_review_documents()
    assert len(documents) == 63
    doc = documents[0]
    for name in PIPELINE_NAMES:
        review = review_document(doc, name)
        assert len(review.audit_rows()) == len(doc.spans)
        assert review.unchanged_count == 0
        assert review.transformation.document_id == doc.document_id
