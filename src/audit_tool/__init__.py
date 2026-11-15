"""Bilingual clinical text de-identification research prototype."""
from .detector import RegexDetector
from .models import Span, PipelineResult, span_from_entity, spans_from_entities, entity_from_span, entities_from_spans
from .pipeline import run_pipeline, audit_external_text
from .transform import transform_text

__all__ = ["RegexDetector", "Span", "PipelineResult", "run_pipeline", "audit_external_text", "transform_text"]

from .categories import classify, unknown_labels
from .config import TransformConfig, standard_pipelines
from .transform import transform_document, transform_entities
