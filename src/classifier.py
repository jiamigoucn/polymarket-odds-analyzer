"""Lightweight market category helpers."""

from __future__ import annotations


WORLD_CUP_TERMS = (
    "world cup",
    "fifa",
    "qualifier",
    "qualification",
    "group stage",
    "golden corridor",
)

MATCH_TERMS = (
    " vs ",
    " v ",
    "match",
    "game",
    "beat",
    "win against",
)

OUTRIGHT_TERMS = (
    "winner",
    "champion",
    "to win",
    "title",
)


def classify_market(title: str, source_category: str | None = None) -> str:
    """Return a stable report category from source data and simple heuristics."""

    if source_category and source_category.strip():
        return source_category.strip()

    normalized = f" {title.lower()} "

    if any(term in normalized for term in WORLD_CUP_TERMS):
        return "world_cup"

    if any(term in normalized for term in MATCH_TERMS):
        return "match"

    if any(term in normalized for term in OUTRIGHT_TERMS):
        return "outright"

    return "uncategorized"
