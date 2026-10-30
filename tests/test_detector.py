import unittest
from audit_tool import RegexDetector
from audit_tool.sample_data import SAMPLES


class DetectorTests(unittest.TestCase):
    def setUp(self):
        self.engine = RegexDetector()

    def test_german_sample(self):
        text = SAMPLES["de"]
        spans = self.engine.detect(text, "de")
        self.assertEqual({"PERSON", "DATE", "LOCATION", "PATIENT_ID", "AGE"}, {s.label for s in spans})
        for span in spans:
            self.assertEqual(text[span.start:span.end], span.text)

    def test_english_sample(self):
        spans = self.engine.detect(SAMPLES["en"], "en")
        self.assertEqual(5, len(spans))
        self.assertTrue(any(s.text == "John Smith" for s in spans))

    def test_invalid_language(self):
        with self.assertRaises(ValueError):
            self.engine.detect("anything", "fr")

    def test_safe_overlap_and_order(self):
        spans = self.engine.detect("Patient Anna Müller from London on 2026-10-12", "en")
        self.assertEqual(spans, sorted(spans, key=lambda s: s.start))
        self.assertTrue(all(a.end <= b.start for a, b in zip(spans, spans[1:])))


if __name__ == "__main__":
    unittest.main()
