# Binance Futures Testnet Trading Bot

A command-line trading bot that places MARKET and LIMIT orders on the
[Binance Futures Testnet](https://testnet.binancefuture.com).

## Project layout

```
trading_bot/
├── bot/
│   ├── __init__.py
│   ├── client.py          # HMAC-signed Binance API wrapper
│   ├── orders.py          # Order placement & output formatting
│   ├── validators.py      # Input validation
│   └── logging_config.py  # Rotating file + console logging
├── cli.py                 # argparse CLI entry point
├── requirements.txt
└── README.md
```

## Setup

### 1. Get Testnet credentials

1. Go to <https://testnet.binancefuture.com> and log in.
2. Navigate to **API Management** and create an API key.
3. Copy the **API Key** and **Secret Key**.

### 2. Install dependencies

```bash
python -m venv .venv
# Windows
.venv\Scripts\activate
# macOS / Linux
source .venv/bin/activate

pip install -r requirements.txt
```

### 3. Set credentials

The bot reads credentials from environment variables (recommended) or CLI flags.

```bash
# Windows PowerShell
$env:BINANCE_API_KEY    = "your_api_key_here"
$env:BINANCE_API_SECRET = "your_secret_here"

# macOS / Linux
export BINANCE_API_KEY="your_api_key_here"
export BINANCE_API_SECRET="your_secret_here"
```

## Usage

```
python cli.py --symbol SYMBOL --side {BUY,SELL} --order-type {MARKET,LIMIT}
              --quantity QTY [--price PRICE] [--time-in-force {GTC,IOC,FOK}]
              [--api-key KEY] [--api-secret SECRET]
              [--log-file PATH] [--json]
```

### Examples

**Place a MARKET BUY order for 0.01 BTC:**
```bash
python cli.py \
  --symbol BTCUSDT \
  --side BUY \
  --order-type MARKET \
  --quantity 0.01
```

**Place a LIMIT SELL order at a specific price:**
```bash
python cli.py \
  --symbol BTCUSDT \
  --side SELL \
  --order-type LIMIT \
  --quantity 0.01 \
  --price 95000
```

**Get the raw JSON response:**
```bash
python cli.py \
  --symbol ETHUSDT \
  --side BUY \
  --order-type MARKET \
  --quantity 0.1 \
  --json
```

**Use explicit credentials instead of env vars:**
```bash
python cli.py \
  --api-key YOUR_KEY \
  --api-secret YOUR_SECRET \
  --symbol BTCUSDT \
  --side BUY \
  --order-type MARKET \
  --quantity 0.001
```

### Output example

```
+----------------------------- Submitting Order ------------------------------+
|   Symbol           BTCUSDT                                                  |
|   Side             BUY                                                      |
|   Type             MARKET                                                   |
|   Quantity         0.01                                                     |
+-----------------------------------------------------------------------------+

+------------------------------- Order Result --------------------------------+
|   Order ID        3279662958                                                |
|   Symbol          BTCUSDT                                                   |
|   Side            BUY                                                       |
|   Type            MARKET                                                    |
|   Status          FILLED                                                    |
|   Orig Qty        0.010                                                     |
|   Executed Qty    0.010                                                     |
|   Avg Price       84321.50000                                               |
|   Limit Price     0                                                         |
|   Update Time     1713097200000                                             |
+-----------------------------------------------------------------------------+
```

Status and side fields are colour-coded in the terminal (green for BUY/FILLED, red for SELL/REJECTED, yellow for NEW/PARTIALLY_FILLED).

Pass `--json` to print the raw API response instead.

## Logging

All API requests, responses, and errors are written to `trading_bot.log`
(configurable with `--log-file`). The file rotates automatically at 5 MB
and keeps 3 backups. Console output is limited to INFO and above.

## Error handling

| Scenario | Behaviour |
|---|---|
| Invalid symbol / side / qty | Validation error printed to stderr, exit code 1 |
| Binance rejects the order | API error code + message printed to stderr, exit code 1 |
| Network unreachable | Connection error message, exit code 1 |
| Request timeout | Timeout message, exit code 1 |

## Assumptions

- Targets the USDT-M Futures Testnet only (`https://testnet.binancefuture.com`). Not intended for live trading.
- Quantity and price are passed as-is to Binance; the exchange enforces symbol-specific precision rules (e.g. step size, tick size).
- `recvWindow` is set to 5000 ms. If your system clock is significantly out of sync, orders may be rejected with a timestamp error.
