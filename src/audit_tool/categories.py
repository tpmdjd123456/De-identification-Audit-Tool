"""Only the PHI labels observed in German GraSCCo_PHI v1 (63 documents)."""

LABEL_TO_CATEGORY = {
    "AGE": "age",
    "CONTACT_EMAIL": "contact",
    "CONTACT_FAX": "contact",
    "CONTACT_PHONE": "contact",
    "DATE": "date",
    "ID": "id",
    "LOCATION_CITY": "place",
    "LOCATION_COUNTRY": "place",
    "LOCATION_HOSPITAL": "place",
    "LOCATION_ORGANIZATION": "employer",
    "LOCATION_STREET": "place",
    "LOCATION_ZIP": "place",
    "NAME_DOCTOR": "person",
    "NAME_EXT": "person",
    "NAME_PATIENT": "person",
    "NAME_RELATIVE": "person",
    "NAME_TITLE": "title",
    "NAME_USERNAME": "id",
    "PROFESSION": "profession",
}


def classify(label: str | None) -> str:
    """Unknown and missing labels fail closed; title is kept distinct from person."""
    return LABEL_TO_CATEGORY.get(label or "", "unknown")


def unknown_labels(labels) -> list[str]:
    """Return unknown *nonempty* label strings; missing kinds are separate data issues."""
    return sorted({x for x in labels if x and x not in LABEL_TO_CATEGORY})
