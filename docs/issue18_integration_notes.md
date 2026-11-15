# Issue #18 — Integration notes and review decisions

This branch combines the existing GraSCCo-tested transformation implementation
with selected features of an independently reviewed alternative. The existing
Streamlit app, `run_pipeline()` and old `transform_text()` interface remain
unchanged. `main` has not been changed.

## Implemented changes

- **Fine-grained categories:** street, ZIP, hospital, city/place, organization /
  provisional employer, profession, title, contact, ID/username and person are
  distinguished. All 19 *observed* nonempty GraSCCo_PHI label types have a
  mapping; one annotation without a kind is kept and redacted as `[UNKNOWN]`.
- **Six strategies:** placeholder, mask, keep, surrogate, date_shift,
  generalize. The Issue #18 P2 policy uses surrogates for direct identifiers,
  a reproducible nonzero offset per document, 5-year age bands, geographic
  region/sector generalization and placeholders for unmapped values.
- **Structured synthetic stand-ins:** IDs, phone and fax values are deterministically
  reshaped while retaining character positions and separators; generated email
  addresses use `@example.invalid`. The mapping is a reproducible research
  stand-in, **not** cryptographically secure or guaranteed to be a safe
  communication endpoint. Check digits are not computed.
- **Safer masking baseline:** P0 now uses fixed `[MASKED]` tokens. Optional
  `mask_style="characters"` preserves separators/length for layout experiments.
- **Detector integration:** `span_from_entity()`, `spans_from_entities()` and
  `transform_entities()` accept the `{start,end,type}` records used by model
  adapters without rewriting existing detection code. Invalid offsets and
  overlaps raise errors.
- **No silent non-keep output:** any generated replacement identical to its
  original is converted to a typed placeholder with a recorded fallback reason.
  This handles year-only and other coarsely specified dates that can remain
  unchanged under rounded offsets.
- **Corpus consistency:** the INCEpTION/UIMA loader retains all annotated PHI
  structures and converts UTF-16 offsets before validating them against the
  Python source text. Corpus text and per-document logs are gitignored.

## Measured results on GraSCCo_PHI v1

- 63 German clinical documents; 1,439 PHI annotation structures, including
  one without an annotation kind; 19 nonempty observed labels; no gold overlaps.
- P0, P1, P2 each transformed all 1,439 annotated occurrences, with **0**
  aligned annotated occurrences left unchanged under non-`keep` policies.
- P2: **82** placeholder fallbacks, including 41 geographic, 2 organization,
  2 age and 37 unparseable dates. Partial-date shifts necessarily lose temporal
  precision. Complete-date intervals were verified in **62/63** documents.
- **37** old identifier strings also appeared somewhere else in the transformed
  P2 documents. These are audit flags, not necessarily failures of annotated
  span replacement; they require manual review and do not measure anonymity.
- Before integration: 27 existing tests passed. After integration: **39 tests
  passed with the corpus**; **37 passed, 2 skipped** without it. Existing demo
  and Python editable install were also smoke-tested.

## Open technical and research questions

1. **Street/ZIP policy:** currently typed placeholders, not arbitrary inferred
   regions or 2-digit postal prefixes. A safe validated hierarchy may be
   investigated later.
2. **Hospital names:** currently generalized to `medizinische Einrichtung`.
   GraSCCo includes station/ward designations under the hospital label, where
   this may be semantically imprecise; compare with typed placeholders in a
   clinical-utility review.
3. **Organizations:** treating every `LOCATION_ORGANIZATION` as an employer is
   provisional. An unknown region results in `[EMPLOYER]` rather than a guess.
4. **German language:** inflected professions, grammatical agreement, eponyms,
   gender cues and aliases are only partially handled. Test with clinical
   linguists and error analysis; no automatic guarantee of medical fidelity.
5. **Determinism and privacy:** seeds/pools intentionally support reproducibility
   but can enable linkage; production pseudonymization would need a different
   threat model and protected secrets.
6. **Evaluation:** all corpus runs use gold labels, not the output of detection
   engines. Evaluate downstream clinical utility and residual indirect
   re-identification risk separately before any safety claims.

## Reproduction

Dataset: [GraSCCo_PHI v1](https://doi.org/10.5281/zenodo.11502329)
(INCEpTION JSON export; clinical text embedded as sofaString). All generated
per-document files remain outside the tracked source tree in `data/runs/`.

```bash
python -m pip install -e ".[dev]"
python -m pytest -q
python -m evaluation.write_inventory_report \
  --source data/grascco/grascco_phi_annotation_json.zip
python -m evaluation.run_transformations \
  --source data/grascco/grascco_phi_annotation_json.zip \
  --output data/runs --summary docs/transformation_run_summary.md
```
