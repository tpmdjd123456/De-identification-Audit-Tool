# GraSCCo Document Review — local Streamlit demonstration

## Setup (Windows PowerShell)

This page is part of the **`issue-18-transformation-strategies` feature branch**.
From the repository directory:

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -e ".[dev,web]"
New-Item -ItemType Directory -Force data\grascco
Copy-Item "$env:USERPROFILE\Downloads\grascco_phi_annotation_json.zip" ".\data\grascco\grascco_phi_annotation_json.zip"
.\.venv\Scripts\python.exe -m pytest -q
.\.venv\Scripts\python.exe -m streamlit run app.py
```

Use any compatible Python 3.10+ environment if Python 3.12 is unavailable.
The dataset ZIP is downloaded from
[GraSCCo_PHI v1](https://doi.org/10.5281/zenodo.11502329). The INCEpTION JSON
exports already include the synthetic German text and gold annotations, so no
second corpus download or manual extraction is needed. Never commit the ZIP or
per-document audit results.

## Instructor walkthrough (about 3–5 minutes)

1. Open the local Streamlit app, normally at `http://localhost:8501`.
2. Choose **GraSCCo Document Review** in the Workflow sidebar. Select a German
   clinical document.
3. Choose **P0 — Masking**, **P1 — Typed placeholders**, and **P2 — Surrogates and
   generalization** in turn. The original gold-annotated text stays on the left;
   the output changes on the right.
4. Inspect counts for **gold spans**, **placeholder fallbacks** and **unchanged
   annotated spans**. Open the audit table to show per-span label, category,
   strategy, original value, replacement, source offsets and fallback reason.
5. Expand the pipeline configuration to show the reproducibility seed, strategy
   settings and document-specific date offset. Export transformed text or JSON
   audit logs if required; these are local files, not GitHub attachments.

## What the page proves, and what it does not

The page exercises the corpus loader and the **Issue #18 transformation layer
with annotated gold identifiers**. Unlike the older *Transform and review*
workflow, this page does **not** infer entity spans using the regex detector.
It does not yet combine the team's Presidio/Qwen/OPF adapters with the UI.

A zero count of unchanged annotated spans means the **specified annotated
occurrences** were replaced, not that the document is anonymous. Reappearance
flags indicate that some original strings still occur elsewhere in the output;
they can be false alarms for short strings and warrant review. The UI does not
establish residual re-identification risk or clinical utility preservation.

When the corpus ZIP is unavailable, the UI presents a setup message instead
of crashing. The legacy synthetic-text demo continues to work without it.

Only use synthetic or appropriately authorized data. The audit JSON exports
original annotated strings. Keep exports local and do not upload them to the
source repository.
