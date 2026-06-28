"""CLI entrypoint for the read-only Polymarket odds analyzer."""

from __future__ import annotations

import argparse
import logging
from pathlib import Path

from .matrix import build_matrix, collect_token_ids
from .polymarket_clob import ClobAPIError, ClobClient
from .polymarket_gamma import GammaAPIError, GammaClient
from .report import write_markdown_report

LOGGER = logging.getLogger(__name__)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Generate a read-only Polymarket BUY/SELL odds matrix report.",
    )
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument(
        "--query",
        help='Market search query, for example: "France Sweden"',
    )
    mode.add_argument(
        "--event-slug",
        help='Event slug for complete event market capture, for example: "world-cup-winner"',
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=500,
        help="Maximum active Gamma markets to scan before local query matching. Ignored with --event-slug.",
    )
    parser.add_argument(
        "--reports-dir",
        default="reports",
        help="Directory where Markdown reports are written.",
    )
    parser.add_argument(
        "--gamma-base-url",
        default="https://gamma-api.polymarket.com",
        help="Gamma API base URL.",
    )
    parser.add_argument(
        "--clob-base-url",
        default="https://clob.polymarket.com",
        help="CLOB API base URL.",
    )
    parser.add_argument(
        "--timeout",
        type=float,
        default=15.0,
        help="HTTP request timeout in seconds.",
    )
    parser.add_argument(
        "--log-level",
        default="INFO",
        choices=("DEBUG", "INFO", "WARNING", "ERROR"),
        help="Logging level.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    logging.basicConfig(
        level=getattr(logging, args.log_level),
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )

    gamma_client = GammaClient(base_url=args.gamma_base_url, timeout=args.timeout)
    clob_client = ClobClient(base_url=args.clob_base_url, timeout=args.timeout)

    try:
        if args.event_slug:
            LOGGER.info("Fetching complete Polymarket event markets for slug: %s", args.event_slug)
            markets = gamma_client.get_event_markets(event_slug=args.event_slug)
            report_label = args.event_slug
        else:
            LOGGER.info("Searching active Polymarket markets for query: %s", args.query)
            markets = gamma_client.search_active_markets(query=args.query, limit=args.limit)
            report_label = args.query
    except (GammaAPIError, ValueError) as exc:
        LOGGER.error("%s", exc)
        return 1

    token_ids = collect_token_ids(markets)
    LOGGER.info("Found %s markets and %s unique token IDs", len(markets), len(token_ids))

    try:
        prices = clob_client.get_prices(token_ids)
    except ClobAPIError as exc:
        LOGGER.warning("%s", exc)
        LOGGER.warning("Continuing with all prices marked as no liquidity")
        prices = {}

    rows = build_matrix(markets, prices)
    report_path = write_markdown_report(
        query=report_label,
        rows=rows,
        reports_dir=Path(args.reports_dir),
    )

    LOGGER.info("Wrote Markdown report: %s", report_path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
