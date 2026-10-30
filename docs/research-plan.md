# Research plan (draft, for team review)

## Project question (from TU Berlin kickoff)
How do de-identification strategies trade off residual risk against utility, and does this depend on document type?

## Initial hypotheses (team proposal)
1. Masking removes more literal identifying information but can reduce clinical usability.
2. Surrogates and generalization can retain more linguistic/clinical information than full masking, without necessarily lowering re-identification risk.
3. Narrative document types may expose more contextual or combinatorial identifiers than structured notes.

## Evaluation design
- Use approved public/synthetic German and English datasets. Check licenses, languages, and gold PHI annotations.
- Define entity-label mapping and stable train/test separation before analysis.
- Run the same documents through each pipeline; use paired comparisons.
- Detection: span-level precision, recall and F1, separately for direct and indirect identifiers.
- Leakage: ground-truth original identifiers remaining after transformation (not the same as a re-identification attack).
- Residual risk: additionally examine rare terms, combinations of quasi-identifiers, and realistic linkage scenarios with explicit assumptions.
- Utility: clinically relevant NER retention, answer preservation or task-specific measures; embedding similarity alone is insufficient.
- By document type: report results per category and examine interactions.
- Compute confidence intervals (e.g. paired bootstrap) and correct for multiple tests where warranted.
- Add a small UX study covering pipeline configuration, risk interpretation, and document review.

## Strong caveats
- All demo results are **illustrative**, never clinical validation.
- Text pattern detection can miss identifiers and cannot establish anonymity.
- Surrogates preserve format, not necessarily confidentiality or original clinical truth.
- Do not feed raw real-patient data into external services or commits.

## Deliverables from kickoff deck
- **10 Dec 2026** midterm: literature, research question, end-to-end prototype.
- **4 Feb 2027** final presentation: working tool, experiments and small user study.
- **25 Feb 2027** report and code: methods, statistics, limitations, contribution table and reproducibility.
