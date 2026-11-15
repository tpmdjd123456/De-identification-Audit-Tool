# GraSCCo_PHI v1 — transformation run summary

Dataset: 2024 German INCEpTION PHI JSON annotation export, DOI: 10.5281/zenodo.11502329.
The archive embeds the full document text in `uima.cas.Sofa.sofaString`.

- **Documents:** 63
- **Annotated spans:** 1439
- **Annotations missing `kind`:** 1 (fail closed as `[UNKNOWN]` in P1/P2)
- **Gold span overlaps:** 0 (all documents; checked before transformation)

## Pipeline comparisons

| Pipeline | Spans | Placeholder fallbacks | Aligned spans unchanged | Gold strings found elsewhere | Interval checks |
|---|---:|---:|---:|---:|---|
| P0_mask | 1439 | 0 | 0 | 14 | 0/0 documents |
| P1_placeholder | 1439 | 0 | 0 | 14 | 0/0 documents |
| P2_surrogate | 1439 | 185 | 0 | 42 | 62/63 documents |

**Interpretation:** A surviving-string check searches the entire transformed document for the original annotated value. Short strings, names repeated outside gold spans, and annotations of substrings can lead to matches even if the originally annotated occurrence was replaced. These are audit flags requiring review, not proven failures of offset replacement. Every annotated occurrence is replaced unless its strategy is explicitly `keep`.

## Categories (same gold spans across all configurations)

| Category | Count |
|---|---:|
| age | 23 |
| contact | 26 |
| date | 694 |
| employer | 2 |
| id | 59 |
| person | 322 |
| place | 171 |
| profession | 2 |
| title | 139 |
| unknown | 1 |

## P2 transformation outcomes

The dictionary coverage figures below refer only to categories using explicit geographic/profession dictionaries. Deterministic name/ID pseudonyms are not dictionary lookups.

| Category | Gold spans | Placeholder fallbacks | Dictionary hit rate |
|---|---:|---:|---:|
| place | 171 | 144 | 15.8% |
| employer | 2 | 2 | 0.0% |
| profession | 2 | 0 | 100.0% |

### Other outcomes

- **Date annotations:** 694; fully parseable dates: 470; partial year/month representations shifted with precision loss: 187; unparsable dates replaced by `[DATE]`: 37.
- **Age annotations:** 23; 5-year band generated for 21; fallback `[AGE]`: 2.
- **Exact strings still found elsewhere:** 42 flags; inspect associated spans; zero annotated occurrences were left unchanged.

Explanations recorded in per-span local logs:

- `partial-month-year`: 131
- `partial-year`: 56
- `unmapped-geographic-hierarchy`: 146
- `unparseable-age`: 2
- `unparseable-date`: 37

## Limitations and interpretation

- This is **gold-annotation oracle transformation**, not end-to-end detector accuracy. Real detector errors require a separate assessment.
- `NAME_TITLE` uses a typed placeholder, since a title is not interchangeable with a person name.
- One original annotation has no `kind` value; it is recorded separately and replaced conservatively.
- Date shifts use one seeded document offset between 1 and 3 years (in either direction); all 63 documents have distinct offsets in this run, though the finite-range hash does not guarantee uniqueness on future corpora. Relative gaps for complete dates are checked, but month/year and year-only representations are necessarily lossy.
- Place and profession dictionaries are intentionally small and conservative; missing mappings become placeholders rather than guessed regions/sectors.
- Person replacements use context cues when available and neutral initial+surname otherwise. Grammatical agreement and ambiguous names are not fully solved.
- In a few original documents, annotations target eponym-like surnames that overlap medical vocabulary. We do not substitute names with disease/medication terms; any gold annotation error needs review separately.
- This is synthetic clinical material, not a measured guarantee of anonymity or clinical utility.
- Full source and transformed document files are excluded from Git and kept under `data/`.
