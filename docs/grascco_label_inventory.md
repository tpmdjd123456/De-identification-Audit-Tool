# German GraSCCo_PHI v1 — gold label inventory

Source: [GraSCCo_PHI v1](https://doi.org/10.5281/zenodo.11502329) (INCEpTION JSON export).
The original German document texts are embedded in the JSON files; all counts below were measured from the uploaded archive.

- Documents: **63**
- PHI annotations: **1439**
- Nonempty observed labels without a category mapping: **0**
- Missing label values: **1** (handled using the `unknown` category and placeholder; not a new invented label)
- Gold annotation span overlaps: **0**

| Actual annotation label | Occurrences | Documents | Assigned category | Mapping assessment |
|---|---:|---:|---|---|
| `<MISSING>` | 1 | 1 | `unknown` | missing annotation kind — fallback |
| `AGE` | 23 | 17 | `age` | mapped from guide/type definition |
| `CONTACT_EMAIL` | 1 | 1 | `contact` | mapped from guide/type definition |
| `CONTACT_FAX` | 7 | 6 | `contact` | mapped from guide/type definition |
| `CONTACT_PHONE` | 18 | 12 | `contact` | mapped from guide/type definition |
| `DATE` | 694 | 63 | `date` | mapped from guide/type definition |
| `ID` | 58 | 30 | `id` | mapped from guide/type definition |
| `LOCATION_CITY` | 59 | 30 | `place` | mapped from guide/type definition |
| `LOCATION_COUNTRY` | 2 | 2 | `place` | mapped from guide/type definition |
| `LOCATION_HOSPITAL` | 36 | 30 | `place` | mapped from guide/type definition |
| `LOCATION_ORGANIZATION` | 2 | 2 | `employer` | provisional mapping — confirm meaning |
| `LOCATION_STREET` | 36 | 19 | `place` | mapped from guide/type definition |
| `LOCATION_ZIP` | 38 | 22 | `place` | mapped from guide/type definition |
| `NAME_DOCTOR` | 154 | 60 | `person` | mapped from guide/type definition |
| `NAME_EXT` | 1 | 1 | `person` | mapped from guide/type definition |
| `NAME_PATIENT` | 166 | 63 | `person` | mapped from guide/type definition |
| `NAME_RELATIVE` | 1 | 1 | `person` | mapped from guide/type definition |
| `NAME_TITLE` | 139 | 58 | `title` | provisional mapping — confirm meaning |
| `NAME_USERNAME` | 1 | 1 | `id` | provisional mapping — confirm meaning |
| `PROFESSION` | 2 | 2 | `profession` | mapped from guide/type definition |

## Classification decisions needing confirmation

- `NAME_TITLE` is kept in a separate **title** category and replaced by a typed placeholder. It is not given a fictional personal name.
- `LOCATION_ORGANIZATION` is mapped to **employer** as a provisional policy category; an organization mention need not be an employer. Both occurrences fall back to `[REGION]` because the region cannot be established reliably.
- `NAME_USERNAME` is mapped to **id**, using a deterministic synthetic username instead of a person name.
- The one annotation lacking `kind` comes from one document and is conservatively transformed using `[UNKNOWN]`.
- The mapping includes **only observed nonempty labels**. If more label kinds appear in a later release, report them before adding mappings.
- Counts are annotated gold spans, not a detector's predictions.
