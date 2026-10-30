import unittest
from audit_tool import run_pipeline, RegexDetector, transform_text
from audit_tool.sample_data import SAMPLES
from audit_tool.models import Span


class TransformTests(unittest.TestCase):
    def test_placeholder_leaves_clinical_diagnosis(self):
        outcome = run_pipeline(SAMPLES["de"], language="de")
        self.assertIn("[PERSON]", outcome.transformed_text)
        self.assertIn("[DATE]", outcome.transformed_text)
        self.assertIn("[AGE]", outcome.transformed_text)
        self.assertIn("Pneumonie", outcome.transformed_text)
        self.assertEqual(0, outcome.unchanged_identifier_count)

    def test_mask_and_keep(self):
        outcome = run_pipeline("Patient John Smith was in London", language="en", strategies={"PERSON": "mask", "LOCATION": "keep"})
        self.assertNotIn("John Smith", outcome.transformed_text)
        self.assertIn("London", outcome.transformed_text)
        self.assertEqual(("London",), outcome.remaining_original_identifiers)

    def test_date_shift_preserves_format(self):
        src = "Patient John Smith on 2026-10-12"
        outcome = run_pipeline(src, language="en", strategies={"DATE": "date_shift"}, shift_days=10)
        self.assertIn("2026-10-22", outcome.transformed_text)

    def test_deterministic_surrogate(self):
        value = "Patient Anna Müller; Patient Anna Müller"
        outcome = run_pipeline(value, strategies={"PERSON": "surrogate"})
        self.assertNotIn("Anna Müller", outcome.transformed_text)
        self.assertEqual(outcome.transformed_text.split("; Patient ")[0].removeprefix("Patient "), outcome.transformed_text.split("; Patient ")[1])

    def test_age_generalization(self):
        result = run_pipeline("Patient John Smith, 67 years old", language="en", strategies={"AGE": "generalize"})
        self.assertIn("60–69 years", result.transformed_text)

    def test_invalid_span_rejected(self):
        with self.assertRaises(ValueError):
            transform_text("hello", [Span(0, 4, "PERSON", "oops")])

    def test_invalid_strategy_rejected(self):
        with self.assertRaises(ValueError):
            transform_text("abc", [], {"PERSON": "magic"})


if __name__ == "__main__":
    unittest.main()
