# polymarket-odds-analyzer

Polymarket single-platform, read-only odds matrix analyzer for World Cup Golden Corridor research.

This project fetches public Polymarket market data, retrieves CLOB BUY/SELL prices, merges quotes into a simple matrix, and writes a Markdown report for manual review.

## Safety Boundaries

This tool is intentionally read-only.

- Does not connect to wallets.
- Does not read private keys.
- Does not sign messages or transactions.
- Does not place orders.
- Does not automate trading.
- Uses only public Polymarket API data.
- Writes Markdown reports only.
- Final trading decisions must be made manually by a human.

Out of scope for v0.1:

- SQLite
- Telegram
- Combo logic
- WebSocket streaming
- Automated trading
- Wallet connection
- 42
- Cross-platform arbitrage

## Requirements

- Python 3.9+
- Network access to Polymarket public APIs

Install dependencies:

```bash
python -m pip install -r requirements.txt
```

## Usage

Run from the project root:

```bash
python -m src.main --query "France Sweden"
```

If your system uses `python3` instead of `python`:

```bash
python3 -m src.main --query "France Sweden"
```

The command writes a Markdown report under `reports/`, for example:

```text
reports/France_Sweden_matrix.md
```

The report includes:

- category
- market title
- outcome
- token_id
- BUY price
- SELL price
- spread
- volume
- liquidity
- url

## How It Works

1. Searches active, non-closed Polymarket markets through the Gamma API.
2. Parses market title, slug, outcomes, CLOB token IDs, volume, and liquidity.
3. Deduplicates all token IDs before querying prices.
4. Calls the CLOB `/prices` endpoint in one batch with both BUY and SELL sides:

```json
[
  {"token_id": "...", "side": "BUY"},
  {"token_id": "...", "side": "SELL"}
]
```

5. Merges BUY and SELL prices for each token.
6. Computes spread when both sides are available.
7. Marks missing prices as `no liquidity` without stopping the program.
8. Writes a Markdown matrix report.

## Notes

Gamma and CLOB API calls use request timeouts. If an API is temporarily unavailable, the CLI exits with a clear error message or writes missing price fields as `no liquidity`, depending on where the failure happens.

This tool is an analysis aid only. It is not investment advice and does not make trading decisions.
