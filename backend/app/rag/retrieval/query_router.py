import re
from typing import Optional

from backend.app.rag.scheme_metadata import SCHEME_METADATA


# Build lookup once
_SCHEME_LOOKUP = {
    "KCC": ["kisan credit card", "kcc"],
    "PMFBY": ["pmfby", "fasal bima", "crop insurance"],
    "PMKISAN": ["pm kisan", "pmkisan", "kisan samman nidhi"],
    "PMKMY": ["pmkmy", "maan-dhan", "pension scheme"],
    "PMKSY": ["pmksy", "sinchai", "irrigation"],
    "RWBCIS": ["rwbcis", "weather based crop insurance"],
}


def detect_scheme_code(query: str) -> Optional[str]:
    """
    Detect if query explicitly refers to exactly ONE scheme.
    Returns scheme_code or None.
    """
    query_lower = query.lower()
    matched = []

    for scheme_code, keywords in _SCHEME_LOOKUP.items():
        for kw in keywords:
            if re.search(rf"\b{re.escape(kw)}\b", query_lower):
                matched.append(scheme_code)
                break

    # Only filter if exactly one scheme is mentioned
    if len(matched) == 1:
        return matched[0]

    return None
