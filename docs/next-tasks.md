# Recommended first GitHub issues

## 1. Dataset investigation and annotation schema
**Acceptance**: dataset inventory with URLs/licensing, German/English coverage, types, and at least one small synthetic gold-annotated test file.

## 2. Integrate Presidio as a second detector
**Acceptance**: adapters return the same `Span` shape; document installed spaCy models and German configuration; no live PHI sent to services.

## 3. Improve identifier span coverage
**Acceptance**: handle name variants, address/phone/email, IDs, terminology, German inflection; error analysis against benchmark labels.

## 4. Pipeline comparisons
**Acceptance**: run two or more configurations on identical texts, store reproducible per-document outputs, compare precision/recall and simple exact-string persistence indicator.

## 5. Residual risk research protocol
**Acceptance**: separate directly observable leakage from quasi-identifier/linkage risk; define adversarial assumptions and limitations, not a single unvalidated risk score.

## 6. Clinical utility study
**Acceptance**: select medically relevant downstream tasks; quantify retention with clear baselines and confidence intervals.

## 7. UX walkthrough and export
**Acceptance**: document view with span navigation and CSV/JSON export; user study plan and ethics/data handling review.
