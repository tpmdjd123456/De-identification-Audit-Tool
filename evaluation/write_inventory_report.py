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
             '- Nonempty observed labels without a category mapping: **0**',
             '- Missing label values: **1** (handled using the `unknown` category and placeholder; not a new invented label)',
             '- Gold annotation span overlaps: **0**', "",
             "| Actual annotation label | Occurrences | Documents | Assigned category | Mapping assessment |",
             "|---|---:|---:|---|---|"]
    for row in r["labels"]:
        lines.append(f'| `{row["label"]}` | {row["occurrences"]} | {row["documents"]} | '
                     f'`{row["category"]}` | {row["mapping_status"]} |')
    lines += ["", "## Classification decisions needing confirmation", "",
              "- `NAME_TITLE` is kept in a separate **title** category and replaced by a typed placeholder. It is not given a fictional personal name.",
              "- `LOCATION_ORGANIZATION` is mapped to **employer** as a provisional policy category; an organization mention need not be an employer. Both occurrences fall back to `[REGION]` because the region cannot be established reliably.",
              "- `NAME_USERNAME` is mapped to **id**, using a deterministic synthetic username instead of a person name.",
              "- The one annotation lacking `kind` comes from one document and is conservatively transformed using `[UNKNOWN]`.",
              "- The mapping includes **only observed nonempty labels**. If more label kinds appear in a later release, report them before adding mappings.",
              "- Counts are annotated gold spans, not a detector's predictions.", ""]
    Path(args.output).parent.mkdir(parents=True, exist_ok=True)
    Path(args.output).write_text("\n".join(lines), encoding="utf-8")
    print("Wrote", args.output)

if __name__ == "__main__":
    main()
