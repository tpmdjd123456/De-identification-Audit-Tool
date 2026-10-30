# Clinical De-identification Audit Tool

**TU Berlin · Quality & Usability Studienprojekt · WiSe 2026/27**

A small, reproducible **research prototype** for building and auditing de-identification pipelines for German and English clinical text. This is **not a production-ready anonymizer** and has **not been validated for real patient data**.

## What already works (v0.1)
- English and German synthetic example notes.
- Transparent rule-based baseline for PERSON, DATE, LOCATION, PATIENT_ID and AGE.
- Type-dependent transformations: placeholder, masking, keep, deterministic surrogate, date shift, and age generalization.
- Side-by-side document review with highlighted detected spans in Streamlit.
- A minimal external-text audit that flags possible identifiers without a gold standard.
- Exact-string persistence checks and gold-span precision/recall/F1 helper.
- Unit tests and GitHub Actions configuration.

**Important:** Age is treated as a quasi-identifier example. The city dictionary and title-dependent name matching are intentionally narrow. The exact-string persistence indicator is *not a re-identification risk score*. False negatives and indirect inference are not handled adequately yet.

## Quick start

Requires **Python 3.10+**.

```bash
python -m venv .venv
source .venv/bin/activate     # Windows PowerShell: .venv\Scripts\Activate.ps1
python -m pip install -e ".[web]"
streamlit run app.py
```

Open the local Streamlit URL. The default examples are fully synthetic. Use the sidebar to choose a language and either transform/review or audit an externally transformed note.

### Dependency-free CLI demo and tests

```bash
python -m pip install -e .
python demo.py
python -m unittest discover -s tests -v
```

## Repository map

```text
app.py                  Web review + external audit
src/audit_tool/
  models.py             Common Span and PipelineResult formats
  detector.py           Simple regex detector (replaceable engine)
  transform.py          Per-type strategies
  pipeline.py           Run and audit functions
  evaluation.py         Gold span precision/recall/F1
  sample_data.py        Synthetic DE/EN examples
  ...
tests/                  Unit tests
docs/research-plan.md   Research scope and measurement plan
docs/next-tasks.md      Proposed GitHub issues
.github/workflows/      CI test matrix
```

## Research question

> How do de-identification strategies trade off residual risk against utility, and does this depend on document type?

Our baseline deliberately does **not** claim to answer this yet. Next: select annotated datasets; add a second detection engine such as Presidio; measure residual identifier leakage and clinically grounded utility; compare results by document type with statistical intervals; run a small user study.

## Project deadlines
- Midterm presentation: **10 December 2026** — literature, question, first end-to-end prototype.
- Final presentation: **4 February 2027** — working system, experiments, small user study.
- Report and code: **25 February 2027** — statistics, limitations, reproducible code.

## Security and data handling

**Do not paste, upload, commit, or deploy real identifying clinical records through this prototype.** Use only synthetic text or data explicitly authorized by the project supervisors, according to legal and institutional data-handling rules. Local execution is preferred. Streamlit has no access-control or encryption layer in this demo; production deployment needs a threat model and security review.

## Team and next steps

See [docs/research-plan.md](docs/research-plan.md) and [docs/next-tasks.md](docs/next-tasks.md). Choose a group coordinator and assign an owner and backup for each work package. Link issues to commits and document who contributed to each component.
