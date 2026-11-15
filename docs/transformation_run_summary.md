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
| P2_surrogate | 1439 | 82 | 0 | 37 | 62/63 documents |

**Interpretation:** A surviving-string check searches the entire transformed document for the original annotated value. Short strings, names repeated outside gold spans, and annotations of substrings can lead to matches even if the originally annotated occurrence was replaced. These are audit flags requiring review, not proven failures of offset replacement. Every annotated occurrence is replaced unless its strategy is explicitly `keep`.

## Categories (same gold spans across all configurations)

| Category | Count |
|---|---:|
| age | 23 |
| contact | 26 |
| date | 694 |
| employer | 2 |
| hospital | 36 |
| id | 59 |
| person | 322 |
| place | 61 |
| profession | 2 |
| street | 36 |
| title | 139 |
| unknown | 1 |
| zip | 38 |

## P2 transformation outcomes

Dictionary hit rates apply only to categories with actual geographic/profession lookup tables. Hospitals use a generic clinical-institution label; streets and ZIP codes use typed placeholders, and names, IDs and contacts use deterministic surrogates. These strategies do not have dictionary hit rates.

| Category | Gold spans | Placeholder fallbacks | Dictionary hit rate |
|---|---:|---:|---:|
| place | 61 | 41 | 32.8% |
| employer | 2 | 2 | 0.0% |
| profession | 2 | 0 | 100.0% |

### Other outcomes

- **Date annotations:** 694; fully parseable dates: 470; partial year/month representations shifted with precision loss: 187; unparsable dates replaced by `[DATE]`: 37.
- **Age annotations:** 23; 5-year band generated for 21; fallback `[AGE]`: 2.
- **Exact strings still found elsewhere:** 37 flags; inspect associated spans; zero annotated occurrences were left unchanged.

Explanations recorded in per-span local logs:

- `partial-month-year`: 131
- `partial-year`: 56
- `unknown-employer-region`: 2
- `unmapped-geographic-hierarchy`: 41
- `unparseable-age`: 2
- `unparseable-date`: 37

## Limitations and interpretation

- This is **gold-annotation oracle transformation**, not end-to-end detector accuracy. Real detector errors require a separate assessment.
- `NAME_TITLE` uses a typed placeholder, since a title is not interchangeable with a person name.
- One original annotation has no `kind` value; it is recorded separately and replaced conservatively.
- Date shifts use one seeded document offset between 1 and 3 years (in either direction); all 63 documents have distinct offsets in this run, though the finite-range hash does not guarantee uniqueness on future corpora. Relative gaps for complete dates are checked, but month/year and year-only representations are necessarily lossy.
- Place and profession dictionaries are intentionally small and conservative; missing mappings become placeholders rather than guessed regions/sectors. Organization names without confirmed geography also fall back.
- Hospitals, streets and postcodes are modeled as distinct categories rather than assuming every location string identifies a city. Generic hospital replacement can lose ward-level clinical context.
- ID and phone surrogates preserve punctuation and character positions; generated values may resemble valid external identifiers, so they are research stand-ins and not suitable for real communication. Email stand-ins use the reserved `.invalid` domain.
- A fixed `[MASKED]` token is the default to avoid revealing original value length; character-based masking remains an optional layout baseline.
- Person replacements use context cues when available and neutral initial+surname otherwise. Grammatical agreement and ambiguous names are not fully solved.
- In a few original documents, annotations target eponym-like surnames that overlap medical vocabulary. We do not substitute names with disease/medication terms; any gold annotation error needs review separately.
- This is synthetic clinical material, not a measured guarantee of anonymity or clinical utility. The 37 exact-string reappearance flags should be manually reviewed, not automatically interpreted as successful re-identification.
- Full source and transformed document files are excluded from Git and kept under `data/`.
