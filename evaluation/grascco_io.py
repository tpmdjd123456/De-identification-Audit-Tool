"""Read embedded German source text and gold annotations from INCEpTION JSON.

Offsets in INCEpTION/UIMA are UTF-16 code units. Translate them to Python
Unicode code-point offsets instead of assuming ASCII/BMP-only data.
"""
from dataclasses import dataclass
from pathlib import Path
from zipfile import ZipFile
import json

from audit_tool.models import Span


@dataclass(frozen=True)
class GraSCCoDocument:
    document_id: str
    text: str
    spans: tuple[Span, ...]


def _u16_to_python_offsets(text: str) -> dict[int, int]:
    indices = {0: 0}
    count = 0
    for i, character in enumerate(text, start=1):
        count += 2 if ord(character) > 0xFFFF else 1
        indices[count] = i
    return indices


def parse_json(payload: dict, document_id: str) -> GraSCCoDocument:
    structures = payload["%FEATURE_STRUCTURES"]
    sofas = [node for node in structures if node.get("%TYPE") == "uima.cas.Sofa"]
    if len(sofas) != 1 or not isinstance(sofas[0].get("sofaString"), str):
        raise ValueError(f"Missing or ambiguous source text: {document_id}")
    text = sofas[0]["sofaString"]
    offsets = _u16_to_python_offsets(text)
    spans = []
    for node in structures:
        if node.get("%TYPE") != "webanno.custom.PHI":
            continue
        try:
            begin, end = offsets[node["begin"]], offsets[node["end"]]
        except KeyError as ex:
            raise ValueError(f"Invalid UTF-16 boundary in {document_id}: {node}") from ex
        label = node.get("kind") or ""
        spans.append(Span(begin, end, label, text[begin:end], source="grascco_gold"))
    return GraSCCoDocument(document_id, text, tuple(sorted(spans, key=lambda s: s.start)))


def load_documents(source: str | Path) -> list[GraSCCoDocument]:
    """Accept the upstream annotation ZIP or an extracted JSON folder."""
    source = Path(source)
    pairs = []
    if source.is_file() and source.suffix.lower() == ".zip":
        with ZipFile(source) as archive:
            for name in sorted(archive.namelist()):
                if name.endswith(".json"):
                    pairs.append((Path(name).name.removesuffix("_phi.json"), json.loads(archive.read(name))))
    elif source.is_dir():
        for path in sorted(source.rglob("*_phi.json")):
            pairs.append((path.name.removesuffix("_phi.json"), json.loads(path.read_text(encoding="utf-8"))))
    else:
        raise FileNotFoundError(f"Expected annotation ZIP or JSON folder: {source}")
    if not pairs:
        raise ValueError("No PHI annotation JSON files found")
    return [parse_json(data, filename) for filename, data in pairs]
