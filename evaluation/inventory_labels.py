"""Print observed GraSCCo_PHI v1 labels and audited mapping status.

Usage: python -m evaluation.inventory_labels --source data/grascco/grascco_phi_annotation_json.zip
"""
import argparse
from collections import Counter, defaultdict
import json

from audit_tool.categories import classify, unknown_labels
from evaluation.grascco_io import load_documents


def build_inventory(documents: list) -> dict:
    counts = Counter()
    frequencies = defaultdict(set)
    for doc in documents:
        for span in doc.spans:
            label = span.label or "<MISSING>"
            counts[label] += 1
            frequencies[label].add(doc.document_id)
    rows = []
    for label in sorted(counts):
        category = classify(None if label == "<MISSING>" else label)
        rows.append({
            "label": label, "occurrences": counts[label],
            "documents": len(frequencies[label]), "category": category,
            "mapping_status": "missing annotation kind — fallback" if label == "<MISSING>" else
                              "provisional mapping — confirm meaning" if label in {"LOCATION_ORGANIZATION", "NAME_USERNAME", "NAME_TITLE"} else
                              "mapped from guide/type definition" if category != "unknown" else
                              "unverified — fallback",
        })
    return {"documents": len(documents), "annotations": sum(counts.values()),
            "unmapped_labels": unknown_labels(k for k in counts if k != "<MISSING>"), "labels": rows}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--source", default="data/grascco/grascco_phi_annotation_json.zip")
    parser.add_argument("--json", default=None, help="Optional JSON file output")
    args = parser.parse_args()
    report = build_inventory(load_documents(args.source))
    print("Label                          Count Docs  Category    Status")
    print("-" * 94)
    for item in report["labels"]:
        print(f'{item["label"]:30s} {item["occurrences"]:5d} {item["documents"]:4d}  '
              f'{item["category"]:11s} {item["mapping_status"]}')
    print("\nJSON inventory:")
    print(json.dumps(report, ensure_ascii=False, indent=2))
    if args.json:
        from pathlib import Path
        Path(args.json).write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")


if __name__ == "__main__":
    main()
