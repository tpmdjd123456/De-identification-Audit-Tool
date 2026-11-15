# Issue #18 — Transformation strategies: data access status

**Status:** Blocked before corpus validation. No claim of completed Issue #18 implementation or corpus evaluation.

**Target repository for this interim work:** [tpmdjd123456/De-identification-Audit-Tool](https://github.com/tpmdjd123456/De-identification-Audit-Tool), a separate repository from the team's `Ner-mine/audit-tool-deidentification`.

## Verified source records

| Resource | Record | DOI | Version | Downloaded? |
| --- | --- | --- | --- | --- |
| German GraSCCo original | https://zenodo.org/records/6539131 | 10.5281/zenodo.6539131 | v1 | No |
| German GraSCCo_PHI annotations | https://zenodo.org/records/11502329 | 10.5281/zenodo.11502329 | v1 | No |

The 2024 PHI record lists `grascco_phi_annotation_json.zip` and `grascco_phi_annotation_xmi.zip`. The original GraSCCo dataset is described as CC BY 4.0; confirm and record the explicit license metadata for each downloaded archive before use. The 2024 record's displayed license field did not establish the license in the available view.

**Access attempt (2026-11-15):** The canonical records were located, but the dataset download failed in this environment (network/DNS access unavailable). The uploaded group-repository snapshot did not contain the `data/grascco/` corpus. No other dataset and no invented corpus have been substituted.

## What remains before implementation can be verified

1. Download both canonical Zenodo releases on a machine with access, verify their versions and licenses, and keep the corpus files out of Git. Only the provenance README in `data/grascco/` is intended for version control.
2. Inspect the **actual** annotation JSON structure and offsets, and write `evaluation/inventory_labels.py` to report each label's occurrence count, document frequency, mapped category and confirmation status.
3. Build/update the category map using the **observed** labels only. Do not invent absent types; unknowns must fall back to placeholders.
4. Implement the supervisor-agreed strategies: surrogate for person/contact/ID; one date offset per document; five-year age bands; region/sector generalization; placeholder fallback; and six configurable operators including `keep`.
5. Verify German inflections, eponym surnames, gender consistency, date formats, span offsets, overlaps, deterministic seeds, and per-span audit logs.
6. Execute `P0_mask`, `P1_placeholder`, and `P2_surrogate` on all original German GraSCCo documents with gold annotations. Report measured spans, dictionaries' actual hit/fallback rates, surviving values, overlap cases and date-interval checks.
7. Run tests including a corpus-dependent test that skips when the data is absent; document any unrelated pre-existing failures in the group repository.

## Not performed

- No new corpus-based code was added; the existing prototype transformation code remains unchanged.
- No dataset counts, label mapping confirmations, dictionary hit rates, or clinical safety results have been measured.
- No real-person re-identification, multilingual translation comparison, detection-adapter modifications, or rare-diagnosis broadening was attempted.

**To resume:** provide the two downloaded Zenodo archives (or run this work in an environment where they can be accessed). This is an honest partial status report, not an implementation-complete PR.
