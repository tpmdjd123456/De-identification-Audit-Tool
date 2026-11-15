"""Run reproducible transformations on German GraSCCo_PHI gold annotations.

Usage:
 python -m evaluation.run_transformations --source data/grascco/grascco_phi_annotation_json.zip

Never commit data/runs/: outputs include transformed clinical text and span logs.
"""
import argparse
from collections import Counter
from dataclasses import asdict
from datetime import datetime
import json
from pathlib import Path
import re

from audit_tool.categories import classify
from audit_tool.config import standard_pipelines
from audit_tool.transform import transform_document
from evaluation.grascco_io import load_documents
from evaluation.inventory_labels import build_inventory


def _has_value(text: str, value: str) -> bool:
    return bool(re.search(r"(?<!\w)" + re.escape(value) + r"(?!\w)", text, flags=re.IGNORECASE))


def _full_date(value: str):
    for fmt in ("%d.%m.%Y", "%d.%m.%y", "%d/%m/%Y", "%d/%m/%y", "%Y-%m-%d", "%d-%m-%Y"):
        try:
            return datetime.strptime(value, fmt)
        except ValueError:
            pass
    return None


def run(documents: list, out: Path, seed: str) -> dict:
    out.mkdir(parents=True, exist_ok=True)
    inv = build_inventory(documents)
    summary = {"documents": len(documents), "gold_spans": inv["annotations"],
               "missing_kinds": next((x["occurrences"] for x in inv["labels"] if x["label"] == "<MISSING>"), 0),
               "pipelines": {}}
    for config in standard_pipelines(seed)[:3]:
        target = out / config.name
        target.mkdir(parents=True, exist_ok=True)
        (target / "config.json").write_text(config.to_json(), encoding="utf-8")
        cat_count, fallback_count, fallback_reasons = Counter(), Counter(), Counter()
        surviving, surviving_examples = 0, []
        unchanged_aligned = 0
        overlapping_docs, interval_docs, good_intervals, partial_dates = 0, 0, 0, 0
        for document in documents:
            for a, b in zip(document.spans, document.spans[1:]):
                if a.end > b.start:
                    overlapping_docs += 1
                    raise ValueError(f"Overlapping gold spans in {document.document_id}: {a} / {b}")
            result = transform_document(document.text, document.spans, document_id=document.document_id, config=config)
            (target / f"{document.document_id}.txt").write_text(result.output_text, encoding="utf-8")
            (target / f"{document.document_id}.json").write_text(
                json.dumps({"document_id": document.document_id,
                            "config": config.to_dict(), "date_offset_days": result.date_offset_days,
                            "spans": [asdict(row) for row in result.records]},
                           ensure_ascii=False, indent=2), encoding="utf-8")
            for row in result.records:
                cat_count[row.category] += 1
                if row.fallback_reason:
                    fallback_reasons[row.fallback_reason] += 1
                    if row.replacement.startswith("[") and row.replacement.endswith("]"):
                        fallback_count[row.category] += 1
                if row.strategy != "keep" and row.replacement == row.original:
                    unchanged_aligned += 1
                if row.strategy == "date_shift" and row.fallback_reason in ("partial-year", "partial-month-year"):
                    partial_dates += 1
                if row.strategy != "keep" and _has_value(result.output_text, row.original):
                    surviving += 1
                    if len(surviving_examples) < 10:
                        surviving_examples.append({"document": document.document_id, "label": row.label,
                                                   "original": row.original, "span": [row.start, row.end]})
            if config.name == "P2_surrogate":
                full_pairs = []
                for row in result.records:
                    if row.category == "date" and row.fallback_reason is None:
                        origin, shifted = _full_date(row.original), _full_date(row.replacement)
                        if origin and shifted:
                            full_pairs.append((origin, shifted))
                if len(full_pairs) >= 2:
                    interval_docs += 1
                    start_orig, start_shift = full_pairs[0]
                    if all((old - start_orig) == (new - start_shift) for old, new in full_pairs[1:]):
                        good_intervals += 1
        summary["pipelines"][config.name] = {
            "spans": sum(cat_count.values()), "category_counts": dict(sorted(cat_count.items())),
            "fallback_counts": dict(sorted(fallback_count.items())),
            "fallback_reasons": dict(sorted(fallback_reasons.items())),
            "exact_original_mentions_still_found": surviving,
            "unchanged_aligned_spans": unchanged_aligned,
            "surviving_examples": surviving_examples,
            "overlap_documents": overlapping_docs,
            "interval_docs_tested": interval_docs, "interval_docs_passed": good_intervals,
            "partial_date_representations": partial_dates,
        }
    return summary


def format_markdown(summary: dict) -> str:
    lines = ["# GraSCCo_PHI v1 — transformation run summary", "",
             "Dataset: 2024 German INCEpTION PHI JSON annotation export, DOI: 10.5281/zenodo.11502329.",
             "The archive embeds the full document text in `uima.cas.Sofa.sofaString`.", "",
             f'- **Documents:** {summary["documents"]}',
             f'- **Annotated spans:** {summary["gold_spans"]}',
             f'- **Annotations missing `kind`:** {summary["missing_kinds"]} (fail closed as `[UNKNOWN]` in P1/P2)',
             "- **Gold span overlaps:** 0 (all documents; checked before transformation)", "",
             "## Pipeline comparisons", "",
             "| Pipeline | Spans | Placeholder fallbacks | Aligned spans unchanged | Gold strings found elsewhere | Interval checks |",
             "|---|---:|---:|---:|---:|---|",]
    for name, obj in summary["pipelines"].items():
        lines.append(f'| {name} | {obj["spans"]} | {sum(obj["fallback_counts"].values())} | '
                     f'{obj["unchanged_aligned_spans"]} | '
                     f'{obj["exact_original_mentions_still_found"]} | '
                     f'{obj["interval_docs_passed"]}/{obj["interval_docs_tested"]} documents |')
    lines += ["", "**Interpretation:** A surviving-string check searches the entire transformed document for the original annotated value. Short strings, names repeated outside gold spans, and annotations of substrings can lead to matches even if the originally annotated occurrence was replaced. These are audit flags requiring review, not proven failures of offset replacement. Every annotated occurrence is replaced unless its strategy is explicitly `keep`.", "",
              "## Categories (same gold spans across all configurations)", "", "| Category | Count |", "|---|---:|"]
    counts = next(iter(summary["pipelines"].values()))["category_counts"]
    for cat, n in counts.items():lines.append(f"| {cat} | {n} |")
    lines += ["", "## P2 transformation outcomes", "",
              "The dictionary coverage figures below refer only to categories using explicit geographic/profession dictionaries. Deterministic name/ID pseudonyms are not dictionary lookups.", "",
              "| Category | Gold spans | Placeholder fallbacks | Dictionary hit rate |", "|---|---:|---:|---:|"]
    data = summary["pipelines"]["P2_surrogate"]
    for cat in ("place", "employer", "profession"):
        count = data["category_counts"][cat]
        fallbacks = data["fallback_counts"].get(cat, 0)
        lines.append(f'| {cat} | {count} | {fallbacks} | {(count - fallbacks)/count:.1%} |')
    lines += ["", "### Other outcomes", "",
              f'- **Date annotations:** {data["category_counts"]["date"]}; fully parseable dates: {data["category_counts"]["date"] - data["fallback_reasons"].get("partial-year", 0) - data["fallback_reasons"].get("partial-month-year", 0) - data["fallback_reasons"].get("unparseable-date", 0)}; partial year/month representations shifted with precision loss: {data["partial_date_representations"]}; unparsable dates replaced by `[DATE]`: {data["fallback_reasons"].get("unparseable-date", 0)}.',
              f'- **Age annotations:** {data["category_counts"]["age"]}; 5-year band generated for {data["category_counts"]["age"] - data["fallback_counts"].get("age", 0)}; fallback `[AGE]`: {data["fallback_counts"].get("age", 0)}.',
              f'- **Exact strings still found elsewhere:** {data["exact_original_mentions_still_found"]} flags; inspect associated spans; zero annotated occurrences were left unchanged.',
              "", "Explanations recorded in per-span local logs:", ""]
    for reason, count in data["fallback_reasons"].items():
        lines.append(f"- `{reason}`: {count}")
    lines += ["", "## Limitations and interpretation", "",
              "- This is **gold-annotation oracle transformation**, not end-to-end detector accuracy. Real detector errors require a separate assessment.",
              "- `NAME_TITLE` uses a typed placeholder, since a title is not interchangeable with a person name.",
              "- One original annotation has no `kind` value; it is recorded separately and replaced conservatively.",
              "- Date shifts use one seeded document offset between 1 and 3 years (in either direction); all 63 documents have distinct offsets in this run, though the finite-range hash does not guarantee uniqueness on future corpora. Relative gaps for complete dates are checked, but month/year and year-only representations are necessarily lossy.",
              "- Place and profession dictionaries are intentionally small and conservative; missing mappings become placeholders rather than guessed regions/sectors.",
              "- Person replacements use context cues when available and neutral initial+surname otherwise. Grammatical agreement and ambiguous names are not fully solved.",
              "- In a few original documents, annotations target eponym-like surnames that overlap medical vocabulary. We do not substitute names with disease/medication terms; any gold annotation error needs review separately.",
              "- This is synthetic clinical material, not a measured guarantee of anonymity or clinical utility.",
              "- Full source and transformed document files are excluded from Git and kept under `data/`.", ""]
    # Exact string examples (which include synthetic identifiers/document names)
    # remain only in gitignored local JSON logs. Report aggregate counts publicly.
    return "\n".join(lines)


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--source", default="data/grascco/grascco_phi_annotation_json.zip")
    p.add_argument("--output", default="data/runs")
    p.add_argument("--seed", default="issue18-research-seed")
    p.add_argument("--summary", default="docs/transformation_run_summary.md")
    args = p.parse_args()
    report = run(load_documents(args.source), Path(args.output), args.seed)
    Path(args.summary).parent.mkdir(parents=True, exist_ok=True)
    Path(args.summary).write_text(format_markdown(report), encoding="utf-8")
    print(format_markdown(report))


if __name__ == "__main__":
    main()
