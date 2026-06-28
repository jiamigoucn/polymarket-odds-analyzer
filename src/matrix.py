"""Merge market metadata and CLOB prices into report rows."""

from __future__ import annotations

from dataclasses import dataclass

from .classifier import classify_market
from .polymarket_clob import TokenPrices
from .polymarket_gamma import GammaMarket


@dataclass(frozen=True)
class MatrixRow:
    category: str
    market_title: str
    outcome: str
    token_id: str
    buy_price: float | None
    sell_price: float | None
    spread: float | None
    volume: float | None
    liquidity: float | None
    url: str


def collect_token_ids(markets: list[GammaMarket]) -> list[str]:
    """Return sorted unique CLOB token IDs from all markets."""

    return sorted({token_id for market in markets for token_id in market.clob_token_ids if token_id})


def build_matrix(
    markets: list[GammaMarket],
    prices: dict[str, TokenPrices],
) -> list[MatrixRow]:
    """Build one deduplicated row per token ID."""

    rows: list[MatrixRow] = []
    seen_token_ids: set[str] = set()

    for market in markets:
        category = classify_market(market.title, market.category)
        for index, token_id in enumerate(market.clob_token_ids):
            if not token_id or token_id in seen_token_ids:
                continue

            seen_token_ids.add(token_id)
            token_prices = prices.get(token_id, TokenPrices())
            rows.append(
                MatrixRow(
                    category=category,
                    market_title=market.title,
                    outcome=_outcome_for_index(market.outcomes, index),
                    token_id=token_id,
                    buy_price=token_prices.buy,
                    sell_price=token_prices.sell,
                    spread=token_prices.spread,
                    volume=market.volume,
                    liquidity=market.liquidity,
                    url=market.url,
                )
            )

    return rows


def _outcome_for_index(outcomes: tuple[str, ...], index: int) -> str:
    if index < len(outcomes) and outcomes[index]:
        return outcomes[index]
    return f"outcome_{index + 1}"
