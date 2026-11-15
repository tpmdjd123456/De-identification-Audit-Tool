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

## Issue #18: corpus-based transformation evaluation

A corpus-backed transformation layer is available in `audit_tool.transform.transform_document`,
with the observed GraSCCo_PHI label mapping in `audit_tool.categories` and reproducible
`TransformConfig` objects in `audit_tool.config`. The new path does not change the
existing rule-based web demo or detection adapters.

Get the German PHI annotation export from [Zenodo v1](https://doi.org/10.5281/zenodo.11502329)
and place `grascco_phi_annotation_json.zip` at `data/grascco/`. The JSON files
contain both `sofaString` source text and gold labels, so there is no need to
copy the separate original text release for this experiment. Corpus files are
ignored by Git; only the provenance README is tracked.

```bash
python -m pip install -e ".[dev]"
python -m evaluation.inventory_labels --source data/grascco/grascco_phi_annotation_json.zip
python -m evaluation.write_inventory_report
python -m evaluation.run_transformations
python -m pytest -q
```

The three pipelines produce JSON configs, per-span audit logs, and transformed
texts under gitignored `data/runs/`. Public aggregate statistics are in
`docs/grascco_label_inventory.md` and `docs/transformation_run_summary.md`.

**Cautions:** These use the *gold* annotations, not the live detector's predictions.
Region/sector dictionaries are deliberately conservative and frequently
fall back to typed placeholders; grammatical agreement, ambiguous dates, and
indirect re-identification risks remain open research problems.

## Issue #18 — GraSCCo transformation layer (draft PR)

The baseline `run_pipeline()` / `transform_text()` API and Streamlit app remain
compatible. The corpus-backed `transform_document()` API adds configurable
per-category transformations and audit records. For detector adapters returning
`{"start": ..., "end": ..., "type": ...}` dictionaries, use `transform_entities()`.

```python
from audit_tool import transform_entities, standard_pipelines

note = "Patientin Anna Müller wurde aufgenommen."
spans = [{"start": 10, "end": 21, "type": "NAME_PATIENT"}]
result = transform_entities(
    note, spans, document_id="example-1", config=standard_pipelines()[2],
)
print(result.output_text)
```

For a corpus-backed run, obtain the German GraSCCo_PHI v1 JSON archive from
[Zenodo](https://doi.org/10.5281/zenodo.11502329) and save it at
`data/grascco/grascco_phi_annotation_json.zip` (the `data/` archive is not
committed). Then run:

```bash
python -m pip install -e ".[dev]"
python -m pytest -q
python -m evaluation.write_inventory_report
python -m evaluation.run_transformations
```

See [`docs/grascco_label_inventory.md`](docs/grascco_label_inventory.md),
[`docs/transformation_run_summary.md`](docs/transformation_run_summary.md), and
[`docs/issue18_integration_notes.md`](docs/issue18_integration_notes.md).

**Research-only:** These results transform annotated gold spans. They do not
measure a complete detector's residual risk and are not evidence that real
clinical text is anonymous. Deterministic surrogates are not security-grade
pseudonyms; do not commit real records, local run logs or the dataset.

## Streamlit: GraSCCo Document Review

The Streamlit interface now includes a **GraSCCo Document Review** workflow in
addition to the original regex demonstration and external-text audit. It uses
the German corpus's **gold PHI annotation spans**, not the regex detector or an
end-to-end detection model. Select one of the 63 documents and one of the
`P0_mask`, `P1_placeholder` or `P2_surrogate` configurations to compare the
source text and the transformed text side by side. The page displays span
counts, fallback and unchanged counts, an audit table, the recorded configuration,
and download options for the transformed text and detailed JSON audit log.

Place the unextracted `grascco_phi_annotation_json.zip` in `data/grascco/` and run:

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -e ".[dev,web]"
.\.venv\Scripts\python.exe -m pytest -q
.\.venv\Scripts\python.exe -m streamlit run app.py
```

The dataset is not stored in Git. Without the ZIP, the interface shows the
required local path while the earlier workflows remain usable. The transformed
texts and audit logs remain on the local computer. These results measure
**transformation of annotated gold spans**, not de-identification quality of
automatically detected identifiers or anonymity. See
[docs/streamlit_grascco_demo.md](docs/streamlit_grascco_demo.md) for a short
demonstration guide and limitations.
