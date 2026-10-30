import unittest
from audit_tool.evaluation import score_exact_spans
from audit_tool.models import Span
from audit_tool import audit_external_text


class EvaluationTests(unittest.TestCase):
    def test_exact_span_scores(self):
        gold = [Span(0, 4, "PERSON", "Anna"), Span(9, 13, "DATE", "2026")]
        pred = [Span(0, 4, "PERSON", "Anna"), Span(9, 13, "LOCATION", "2026")]
        scores = score_exact_spans(gold, pred)
        self.assertEqual((1, 1, 1), (scores.tp, scores.fp, scores.fn))
        self.assertEqual(0.5, scores.f1)

    def test_empty_gold_and_prediction(self):
        scores = score_exact_spans([], [])
        self.assertEqual((1.0, 1.0, 1.0), (scores.precision, scores.recall, scores.f1))

    def test_external_audit(self):
        flags = audit_external_text("Patient [PERSON] was treated in Berlin", language="en")
        self.assertEqual(["LOCATION"], [s.label for s in flags])


if __name__ == "__main__":
    unittest.main()
