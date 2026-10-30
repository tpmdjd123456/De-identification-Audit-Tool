"""Gold-standard comparison: span-level exact-match precision/recall/F1."""
from dataclasses import dataclass
from typing import Sequence
from .models import Span


@dataclass(frozen=True)
class DetectionMetrics:
    tp: int
    fp: int
    fn: int
    precision: float
    recall: float
    f1: float


def score_exact_spans(gold: Sequence[Span], predicted: Sequence[Span]) -> DetectionMetrics:
    """Compare exact (start, end, label); empty gold+pred = 1 for all rates."""
    expected = {(s.start, s.end, s.label) for s in gold}
    actual = {(s.start, s.end, s.label) for s in predicted}
    tp = len(expected & actual)
    fp = len(actual - expected)
    fn = len(expected - actual)
    precision = tp / (tp + fp) if tp + fp else (1.0 if not expected else 0.0)
    recall = tp / (tp + fn) if tp + fn else 1.0
    f1 = 2 * precision * recall / (precision + recall) if precision + recall else 0.0
    return DetectionMetrics(tp, fp, fn, precision, recall, f1)
