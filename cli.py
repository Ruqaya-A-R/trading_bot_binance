#!/usr/bin/env python3
"""CLI entry point for the Binance Futures Testnet trading bot."""

from __future__ import annotations

import argparse
import json
import os
import sys

import requests
from rich.console import Console

from bot.client import BinanceAPIError, BinanceClient
from bot.logging_config import get_logger, setup_logging
from bot.orders import place_order, print_order_summary, print_request_summary
from bot.validators import ValidationError


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="trading-bot",
        description="Place orders on Binance Futures Testnet.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )

    # Credentials — prefer env vars, allow explicit flags for convenience
    parser.add_argument(
        "--api-key",
        default=os.environ.get("BINANCE_API_KEY", ""),
        help="Binance API key (or set BINANCE_API_KEY env var).",
    )
    parser.add_argument(
        "--api-secret",
        default=os.environ.get("BINANCE_API_SECRET", ""),
        help="Binance API secret (or set BINANCE_API_SECRET env var).",
    )

    # Order parameters
    parser.add_argument(
        "--symbol",
        required=True,
        help="Trading pair symbol, e.g. BTCUSDT.",
    )
    parser.add_argument(
        "--side",
        required=True,
        choices=["BUY", "SELL"],
        type=str.upper,
        help="Order side.",
    )
    parser.add_argument(
        "--order-type",
        required=True,
        dest="order_type",
        choices=["MARKET", "LIMIT"],
        type=str.upper,
        help="Order type.",
    )
    parser.add_argument(
        "--quantity",
        required=True,
        type=float,
        help="Order quantity (in base asset units).",
    )
    parser.add_argument(
        "--price",
        type=float,
        default=None,
        help="Limit price (required for LIMIT orders, omit for MARKET).",
    )
    parser.add_argument(
        "--time-in-force",
        dest="time_in_force",
        default="GTC",
        choices=["GTC", "IOC", "FOK"],
        help="Time-in-force for LIMIT orders.",
    )

    # Output / debug
    parser.add_argument(
        "--log-file",
        default="trading_bot.log",
        help="Path to the log file.",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        dest="output_json",
        help="Print the raw API response as JSON instead of the summary.",
    )

    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()

    # Bootstrap logging before doing anything that could fail
    setup_logging(log_file=args.log_file)
    logger = get_logger("cli")

    console = Console()
    err_console = Console(stderr=True)

    # Validate credentials
    if not args.api_key or not args.api_secret:
        parser.error(
            "API key and secret are required. "
            "Set BINANCE_API_KEY / BINANCE_API_SECRET env vars or use --api-key / --api-secret."
        )

    logger.info(
        "Starting order: symbol=%s side=%s type=%s qty=%s price=%s",
        args.symbol,
        args.side,
        args.order_type,
        args.quantity,
        args.price,
    )

    if not args.output_json:
        print_request_summary(
            symbol=args.symbol,
            side=args.side,
            order_type=args.order_type,
            quantity=args.quantity,
            price=args.price,
            time_in_force=args.time_in_force,
            console=console,
        )

    client = BinanceClient(api_key=args.api_key, api_secret=args.api_secret)

    try:
        response = place_order(
            client=client,
            symbol=args.symbol,
            side=args.side,
            order_type=args.order_type,
            quantity=args.quantity,
            price=args.price,
            time_in_force=args.time_in_force,
        )
    except ValidationError as exc:
        logger.error("Validation error: %s", exc)
        err_console.print(f"[bold red]Validation error:[/bold red] {exc}")
        return 1
    except BinanceAPIError as exc:
        logger.error("Binance API error %s: %s", exc.code, exc.message)
        err_console.print(f"[bold red]Binance API error {exc.code}:[/bold red] {exc.message}")
        return 1
    except requests.ConnectionError as exc:
        logger.error("Network connection error: %s", exc)
        err_console.print(f"[bold red]Connection error:[/bold red] Could not reach Binance — {exc}")
        return 1
    except requests.Timeout as exc:
        logger.error("Request timed out: %s", exc)
        err_console.print(f"[bold red]Timeout:[/bold red] {exc}")
        return 1
    except requests.RequestException as exc:
        logger.error("HTTP error: %s", exc)
        err_console.print(f"[bold red]HTTP error:[/bold red] {exc}")
        return 1

    if args.output_json:
        print(json.dumps(response, indent=2))
    else:
        print_order_summary(response, console)

    return 0


if __name__ == "__main__":
    sys.exit(main())
