"""Markdown report writer for odds matrices."""

from __future__ import annotations

import re
from pathlib import Path

from .matrix import MatrixRow


REPORT_COLUMNS = (
    "category",
    "market title",
    "outcome",
    "token_id",
    "BUY price",
    "SELL price",
    "spread",
    "volume",
    "liquidity",
    "url",
)


def write_markdown_report(
    query: str,
    rows: list[MatrixRow],
    reports_dir: Path | str = "reports",
) -> Path:
    """Write a Markdown matrix report and return the path."""

    output_dir = Path(reports_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    path = output_dir / f"{_safe_filename(query)}_matrix.md"
    path.write_text(_render_report(query, rows), encoding="utf-8")
    return path


def _render_report(query: str, rows: list[MatrixRow]) -> str:
    lines = [
        f"# Polymarket Odds Matrix: {query}",
        "",
        "Read-only report generated from public Polymarket API data.",
        "",
        f"- Markets rows: {len(rows)}",
        "- Missing BUY or SELL prices are marked as `no liquidity`.",
        "",
        "| " + " | ".join(REPORT_COLUMNS) + " |",
        "| " + " | ".join("---" for _ in REPORT_COLUMNS) + " |",
    ]

    for row in rows:
        lines.append(
            "| "
            + " | ".join(
                [
                    _escape(row.category),
                    _escape(row.market_title),
                    _escape(row.outcome),
                    _escape(row.token_id),
                    _format_price(row.buy_price),
                    _format_price(row.sell_price),
                    _format_price(row.spread),
                    _format_number(row.volume),
                    _format_number(row.liquidity),
                    _escape(row.url),
                ]
            )
            + " |"
        )

    if not rows:
        lines.extend(["", "No active markets with CLOB token IDs were found for this query."])

    lines.append("")
    return "\n".join(lines)


def _safe_filename(value: str) -> str:
    cleaned = re.sub(r"[^A-Za-z0-9._-]+", "_", value.strip())
    cleaned = cleaned.strip("._-")
    return cleaned or "query"


def _format_price(value: float | None) -> str:
    if value is None:
        return "no liquidity"
    return f"{value:.4f}".rstrip("0").rstrip(".")


def _format_number(value: float | None) -> str:
    if value is None:
        return ""
    return f"{value:.2f}".rstrip("0").rstrip(".")


def _escape(value: str) -> str:
    return str(value).replace("|", "\\|").replace("\n", " ")
