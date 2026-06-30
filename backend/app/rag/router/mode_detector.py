from typing import Literal

Mode = Literal["information", "advisory"]


ADVISORY_KEYWORDS = [
    "which scheme should",
    "what should i apply",
    "recommend",
    "suggest",
    "best scheme",
    "eligible for me",
    "based on my",
]


def detect_mode(query: str) -> Mode:
    """
    Decide whether query is informational or advisory.

    Advisory mode is DISABLED for now, but detection is kept
    for future extension.
    """
    q = query.lower()

    for phrase in ADVISORY_KEYWORDS:
        if phrase in q:
            return "advisory"

    return "information"
