# AGENTS.md

## Project Role

This repository is a Polymarket single-platform, read-only odds matrix analyzer for World Cup Golden Corridor research.

## Non-Negotiable Safety Rules

- Do not add wallet connection code.
- Do not read or request private keys.
- Do not add signing logic.
- Do not add order placement logic.
- Do not add automated trading logic.
- Do not add cross-platform arbitrage execution.
- Use only public Polymarket API data.
- Keep output limited to analysis artifacts such as Markdown reports.

## Implementation Guidance

- Keep logging professional and factual.
- Avoid promotional or exaggerated language.
- Keep API clients small, explicit, and read-only.
- Missing CLOB prices must not crash report generation; mark them as `no liquidity`.
- Prefer simple data structures and focused modules for v0.1.
- Do not add SQLite, Telegram, Combo, WebSocket, wallet, 42, or arbitrage features unless a later version explicitly changes scope.

## Expected CLI

```bash
python -m src.main --query "France Sweden"
```

## Expected Output

Reports are written to `reports/<query>_matrix.md`, with filenames sanitized for filesystem safety.
