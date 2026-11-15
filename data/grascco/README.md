# German GraSCCo_PHI corpus provenance

- Dataset: **GraSCCo_PHI — Graz Synthetic Clinical text Corpus with Protected Health Information Annotations**
- Creators: Christina Lohr et al.
- Record: https://zenodo.org/records/11502329
- DOI: **10.5281/zenodo.11502329**
- Version: **v1 (2024-09-09)**
- Annotation archive: `grascco_phi_annotation_json.zip` (uploaded by project contributor)
- Processed locally on: **2026-11-15**
- License: **CC BY 4.0** as reported in the BigScience Biomedical GraSCCo issue (https://github.com/bigscience-workshop/biomedical/issues/950). Confirm against the canonical Zenodo Rights section before redistribution.
- Related original GraSCCo (v1): https://zenodo.org/records/6539131, DOI 10.5281/zenodo.6539131
- Annotation guide: *De-Identifikation deutschsprachiger klinischer Texte in GeMTeX – Annotationsleitlinien für identifizierende Merkmale*, first version (2024-09-09), associated with the same PHI Zenodo record.

The **INCEpTION JSON annotation export contains the complete German document text** in each `uima.cas.Sofa.sofaString` and gold PHI spans in `webanno.custom.PHI`; a separate copy of the unannotated text is not required for this transformation experiment. This is distinct from downloading and independently checking the upstream original archive.

The archive is kept at `data/grascco/grascco_phi_annotation_json.zip` and **is gitignored**. All per-document outputs and configs go to gitignored `data/runs/`. Do not commit corpus text, annotation files, identifiers, or transformed documents.
