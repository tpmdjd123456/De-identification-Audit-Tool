"""Gold GraSCCo_PHI v1 label -> narrowly scoped transformation category.

Keep contact, ID, usernames, street addresses, postcodes, institutions, and
person titles distinct. Unknown/missing labels are **never** passed through.
The inventory is defined by the observed corpus rather than hypothetical tags.
"""

LABEL_TO_CATEGORY: dict[str, str] = {
    "AGE": "age",
    "CONTACT_EMAIL": "contact",
    "CONTACT_FAX": "contact",
    "CONTACT_PHONE": "contact",
    "DATE": "date",
    "ID": "id",
    "LOCATION_CITY": "place",
    "LOCATION_COUNTRY": "place",
    "LOCATION_HOSPITAL": "hospital",
    "LOCATION_ORGANIZATION": "employer",
    "LOCATION_STREET": "street",
    "LOCATION_ZIP": "zip",
    "NAME_DOCTOR": "person",
    "NAME_EXT": "person",
    "NAME_PATIENT": "person",
    "NAME_RELATIVE": "person",
    "NAME_TITLE": "title",
    "NAME_USERNAME": "id",
    "PROFESSION": "profession",
}


def classify(label: str | None) -> str:
    """Map a PHI label, returning the fail-closed ``unknown`` category.

    Normalization supports adapters with varied casing while preserving the
    labels recorded in gold annotations and evaluation outputs.
    """
    if not label:
        return "unknown"
    if label in LABEL_TO_CATEGORY:
        return LABEL_TO_CATEGORY[label]
    return LABEL_TO_CATEGORY.get(label.upper(), "unknown")


def unknown_labels(labels) -> list[str]:
    """Return nonempty labels with no confirmed GraSCCo classification."""
    return sorted({x for x in labels if x and classify(x) == "unknown"})
