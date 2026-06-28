"""Read-only client for Polymarket Gamma market data."""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass
from typing import Any

import requests

LOGGER = logging.getLogger(__name__)


DEFAULT_GAMMA_BASE_URL = "https://gamma-api.polymarket.com"
POLYMARKET_EVENT_BASE_URL = "https://polymarket.com/event"


class GammaAPIError(RuntimeError):
    """Raised when Gamma market data cannot be fetched."""


@dataclass(frozen=True)
class GammaMarket:
    """Normalized market fields needed by the matrix report."""

    title: str
    slug: str
    outcomes: tuple[str, ...]
    clob_token_ids: tuple[str, ...]
    volume: float | None
    liquidity: float | None
    category: str | None
    url: str


class GammaClient:
    """Small read-only Gamma API client."""

    def __init__(
        self,
        base_url: str = DEFAULT_GAMMA_BASE_URL,
        timeout: float = 15.0,
        session: requests.Session | None = None,
    ) -> None:
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self.session = session or requests.Session()

    def search_active_markets(self, query: str, limit: int = 500) -> list[GammaMarket]:
        """Search active markets and normalize the response.

        Gamma market endpoints may ignore search-like query parameters, so this
        method scans active markets and applies local matching before reporting.
        """

        query = query.strip()
        if not query:
            raise ValueError("query must not be empty")

        raw_markets: list[dict[str, Any]] = []
        seen_market_keys: set[str] = set()

        for params in self._active_market_pages(limit=limit):
            data = self._get_json("/markets", params=params)
            items = _extract_market_items(data)
            for item in items:
                key = str(item.get("id") or item.get("conditionId") or item.get("slug") or item)
                if key in seen_market_keys:
                    continue
                seen_market_keys.add(key)
                raw_markets.append(item)
            if len(items) < int(params["limit"]):
                break

        filtered = [item for item in raw_markets if _matches_query(item, query)]

        markets = [_parse_market(item) for item in filtered]
        markets = [market for market in markets if market.clob_token_ids]

        if not markets:
            LOGGER.warning("No active markets with CLOB token IDs found for query: %s", query)

        return markets

    def _active_market_pages(self, limit: int) -> list[dict[str, Any]]:
        max_markets = max(1, limit)
        page_size = min(100, max_markets)
        pages: list[dict[str, Any]] = []

        for offset in range(0, max_markets, page_size):
            current_limit = min(page_size, max_markets - offset)
            pages.append(
                {
                    "active": "true",
                    "closed": "false",
                    "limit": str(current_limit),
                    "offset": str(offset),
                }
            )

        return pages

    def _get_json(self, path: str, params: dict[str, Any]) -> Any:
        url = f"{self.base_url}{path}"
        try:
            response = self.session.get(url, params=params, timeout=self.timeout)
            response.raise_for_status()
            return response.json()
        except requests.RequestException as exc:
            raise GammaAPIError(f"Gamma API request failed: {exc}") from exc
        except ValueError as exc:
            raise GammaAPIError("Gamma API returned invalid JSON") from exc


def _extract_market_items(data: Any) -> list[dict[str, Any]]:
    if isinstance(data, list):
        return [item for item in data if isinstance(item, dict)]

    if not isinstance(data, dict):
        return []

    for key in ("markets", "data", "results"):
        value = data.get(key)
        if isinstance(value, list):
            return [item for item in value if isinstance(item, dict)]

    return []


def _parse_market(item: dict[str, Any]) -> GammaMarket:
    title = _first_text(item, "title", "question", "name") or "Untitled market"
    slug = _first_text(item, "slug", "marketSlug") or ""
    outcomes = tuple(_parse_string_list(item.get("outcomes")))
    clob_token_ids = tuple(_parse_string_list(item.get("clobTokenIds") or item.get("clob_token_ids")))
    category = _first_text(item, "category", "categorySlug", "tag")
    volume = _first_float(item, "volume", "volumeNum", "volume_num")
    liquidity = _first_float(item, "liquidity", "liquidityNum", "liquidity_num")
    url = _market_url(item, slug)

    return GammaMarket(
        title=title,
        slug=slug,
        outcomes=outcomes,
        clob_token_ids=clob_token_ids,
        volume=volume,
        liquidity=liquidity,
        category=category,
        url=url,
    )


def _parse_string_list(value: Any) -> list[str]:
    if value is None:
        return []

    if isinstance(value, str):
        stripped = value.strip()
        if not stripped:
            return []
        try:
            parsed = json.loads(stripped)
        except json.JSONDecodeError:
            return [stripped]
        return _parse_string_list(parsed)

    if isinstance(value, (list, tuple)):
        return [str(item) for item in value if item is not None and str(item).strip()]

    return [str(value)]


def _first_text(item: dict[str, Any], *keys: str) -> str | None:
    for key in keys:
        value = item.get(key)
        if value is not None and str(value).strip():
            return str(value).strip()
    return None


def _first_float(item: dict[str, Any], *keys: str) -> float | None:
    for key in keys:
        value = item.get(key)
        if value is None or value == "":
            continue
        try:
            return float(value)
        except (TypeError, ValueError):
            LOGGER.debug("Could not parse numeric field %s=%r", key, value)
    return None


def _market_url(item: dict[str, Any], slug: str) -> str:
    explicit_url = _first_text(item, "url")
    if explicit_url:
        return explicit_url

    event_slug = _first_text(item, "eventSlug", "event_slug")
    if event_slug and slug:
        return f"{POLYMARKET_EVENT_BASE_URL}/{event_slug}/{slug}"

    if slug:
        return f"{POLYMARKET_EVENT_BASE_URL}/{slug}"

    return "https://polymarket.com"


def _matches_query(item: dict[str, Any], query: str) -> bool:
    terms = [part.lower() for part in query.split() if part.strip()]
    if not terms:
        return True

    searchable_keys = {"title", "question", "name", "slug", "description", "outcomes", "category"}
    haystack = " ".join(str(value) for key, value in item.items() if key in searchable_keys).lower()
    return all(term in haystack for term in terms)
