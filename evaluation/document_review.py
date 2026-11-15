"""Small, testable view model for the local GraSCCo document review UI.

Uses the gold PHI annotations embedded in the GraSCCo_PHI archive, not the
prototype regex detector. Nothing is transmitted to third-party services.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass
from pathlib import Path
import re

from audit_tool.config import standard_pipelines
from audit_tool.models import DocumentTransformation
from audit_tool.transform import transform_document
from evaluation.grascco_io import GraSCCoDocument, load_documents

DEFAULT_ARCHIVE = Path(__file__).resolve().parents[1] / "data" / "grascco" / "grascco_phi_annotation_json.zip"
PIPELINE_NAMES = ("P0_mask", "P1_placeholder", "P2_surrogate")


@dataclass(frozen=True)
class Review:
    document: GraSCCoDocument
    transformation: DocumentTransformation
    fallback_count: int
    unchanged_count: int
    original_string_flags: int

    def audit_rows(self) -> list[dict]:
        return [asdict(row) for row in self.transformation.records]


def load_review_documents(archive: str | Path = DEFAULT_ARCHIVE) -> list[GraSCCoDocument]:
    """Return GraSCCo's original German text and its gold annotation spans."""
    return load_documents(archive)


def review_document(
    document: GraSCCoDocument, pipeline_name: str, *, seed: str = "issue18-research-seed"
) -> Review:
    """Run one of the three committed comparison pipelines on a document."""
    configs = {config.name: config for config in standard_pipelines(seed)[:3]}
    if pipeline_name not in configs:
        raise ValueError(f"Unknown comparison pipeline {pipeline_name!r}")

    transformed = transform_document(
        document.text, document.spans, document_id=document.document_id, config=configs[pipeline_name]
    )
    rows = transformed.records
    flags = sum(
        bool(re.search(r"(?<!\w)" + re.escape(item.original) + r"(?!\w)", transformed.output_text, re.I))
        for item in rows
        if item.strategy != "keep"
    )
    return Review(
        document=document,
        transformation=transformed,
        fallback_count=sum(bool(row.fallback_reason) and row.replacement.startswith("[")
                           and row.replacement.endswith("]") for row in rows),
        unchanged_count=sum(row.strategy != "keep" and row.original == row.replacement for row in rows),
        original_string_flags=flags,
    )
