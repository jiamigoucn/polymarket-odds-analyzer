"""Read-only client for Polymarket CLOB prices."""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Any

import requests

LOGGER = logging.getLogger(__name__)


DEFAULT_CLOB_BASE_URL = "https://clob.polymarket.com"
SIDES = ("BUY", "SELL")


class ClobAPIError(RuntimeError):
    """Raised when CLOB prices cannot be fetched."""


@dataclass(frozen=True)
class TokenPrices:
    """BUY and SELL prices for one token."""

    buy: float | None = None
    sell: float | None = None

    @property
    def spread(self) -> float | None:
        if self.buy is None or self.sell is None:
            return None
        return self.sell - self.buy


class ClobClient:
    """Small read-only CLOB API client."""

    def __init__(
        self,
        base_url: str = DEFAULT_CLOB_BASE_URL,
        timeout: float = 15.0,
        session: requests.Session | None = None,
    ) -> None:
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self.session = session or requests.Session()

    def get_prices(self, token_ids: list[str]) -> dict[str, TokenPrices]:
        """Fetch BUY and SELL prices for unique token IDs."""

        unique_token_ids = sorted({token_id for token_id in token_ids if token_id})
        if not unique_token_ids:
            return {}

        payload = [
            {"token_id": token_id, "side": side}
            for token_id in unique_token_ids
            for side in SIDES
        ]

        url = f"{self.base_url}/prices"
        try:
            response = self.session.post(url, json=payload, timeout=self.timeout)
            response.raise_for_status()
            data = response.json()
        except requests.RequestException as exc:
            raise ClobAPIError(f"CLOB API request failed: {exc}") from exc
        except ValueError as exc:
            raise ClobAPIError("CLOB API returned invalid JSON") from exc

        if not data:
            LOGGER.warning("CLOB returned an empty price response; marking prices as no liquidity")
            return {token_id: TokenPrices() for token_id in unique_token_ids}

        parsed = _parse_prices_response(data)
        for token_id in unique_token_ids:
            parsed.setdefault(token_id, TokenPrices())
        return parsed


def _parse_prices_response(data: Any) -> dict[str, TokenPrices]:
    raw: dict[str, dict[str, float | None]] = {}

    def ensure(token_id: str) -> dict[str, float | None]:
        return raw.setdefault(token_id, {"BUY": None, "SELL": None})

    if isinstance(data, dict):
        if isinstance(data.get("prices"), list):
            _consume_price_entries(data["prices"], ensure)
        elif isinstance(data.get("prices"), dict):
            _consume_mapping(data["prices"], ensure)
        else:
            _consume_mapping(data, ensure)
    elif isinstance(data, list):
        _consume_price_entries(data, ensure)

    return {
        token_id: TokenPrices(buy=sides.get("BUY"), sell=sides.get("SELL"))
        for token_id, sides in raw.items()
    }


def _consume_price_entries(
    entries: list[Any],
    ensure: Any,
) -> None:
    for entry in entries:
        if not isinstance(entry, dict):
            continue
        token_id = str(entry.get("token_id") or entry.get("tokenId") or "").strip()
        side = str(entry.get("side") or "").upper()
        price = _parse_price(entry.get("price"))
        if token_id and side in SIDES:
            ensure(token_id)[side] = price


def _consume_mapping(
    mapping: dict[Any, Any],
    ensure: Any,
) -> None:
    for token_id, value in mapping.items():
        token_id_text = str(token_id).strip()
        if not token_id_text:
            continue

        if isinstance(value, dict):
            for side in SIDES:
                price = _parse_price(value.get(side) or value.get(side.lower()))
                if price is not None:
                    ensure(token_id_text)[side] = price
        else:
            LOGGER.debug("Skipping unrecognized CLOB price value for token %s", token_id_text)


def _parse_price(value: Any) -> float | None:
    if value is None or value == "":
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        LOGGER.debug("Could not parse CLOB price value: %r", value)
        return None
