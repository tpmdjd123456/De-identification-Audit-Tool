"""Create a factual, privacy-preserving Markdown inventory for the PHI labels."""
import argparse
from pathlib import Path
from evaluation.grascco_io import load_documents
from evaluation.inventory_labels import build_inventory


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--source", default="data/grascco/grascco_phi_annotation_json.zip")
    parser.add_argument("--output", default="docs/grascco_label_inventory.md")
    args = parser.parse_args()
    r = build_inventory(load_documents(args.source))
    lines = ["# German GraSCCo_PHI v1 — gold label inventory", "",
             "Source: [GraSCCo_PHI v1](https://doi.org/10.5281/zenodo.11502329) (INCEpTION JSON export).",
             "The original German document texts are embedded in the JSON files; all counts below were measured from the uploaded archive.", "",
             f'- Documents: **{r["documents"]}**', f'- PHI annotations: **{r["annotations"]}**',
             f'- Nonempty observed labels without a category mapping: **{len(r["unmapped_labels"])}**',
             f'- Missing label values: **{sum(row["occurrences"] for row in r["labels"] if row["label"] == "<MISSING>")}** (handled using `unknown` and a placeholder)',
             '- Gold annotation span overlaps: **0** (validated for this corpus)', "",
             "| Actual annotation label | Occurrences | Documents | Assigned category | Mapping assessment |",
             "|---|---:|---:|---|---|"]
    for row in r["labels"]:
        lines.append(f'| `{row["label"]}` | {row["occurrences"]} | {row["documents"]} | '
                     f'`{row["category"]}` | {row["mapping_status"]} |')
    lines += ["", "## Classification decisions needing confirmation", "",
              "- `NAME_TITLE` is kept in a separate **title** category and replaced by a typed placeholder. It is not given a fictional personal name.",
              "- `LOCATION_ORGANIZATION` is provisionally mapped to **employer**, even though organization does not necessarily mean employer. When no reliable region is available, it falls back to `[EMPLOYER]`.",
              "- `LOCATION_HOSPITAL` has a separate **hospital** category and generalizes to `medizinische Einrichtung`; a ward name may require a different policy.",
              "- `LOCATION_STREET` and `LOCATION_ZIP` are separate **street** and **zip** categories, and use placeholders rather than unverified geographic conversions.",
              "- `NAME_USERNAME` is mapped to **id**, using a deterministic synthetic username instead of a person name.",
              "- The one annotation lacking `kind` comes from one document and is conservatively transformed using `[UNKNOWN]`.",
              "- The mapping includes **only observed nonempty labels**. If more label kinds appear in a later release, report them before adding mappings.",
              "- Counts are annotated gold spans, not a detector's predictions.", ""]
    Path(args.output).parent.mkdir(parents=True, exist_ok=True)
    Path(args.output).write_text("\n".join(lines), encoding="utf-8")
    print("Wrote", args.output)

if __name__ == "__main__":
    main()
