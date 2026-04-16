"""High-level order placement logic."""

from __future__ import annotations

from typing import Any

from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.text import Text

from bot.client import BinanceClient
from bot.logging_config import get_logger
from bot.validators import validate_order_params

logger = get_logger("orders")

# Default time-in-force for LIMIT orders
DEFAULT_TIME_IN_FORCE = "GTC"


def _build_order_payload(
    symbol: str,
    side: str,
    order_type: str,
    quantity: float,
    price: float | None = None,
    time_in_force: str = DEFAULT_TIME_IN_FORCE,
) -> dict:
    payload: dict[str, Any] = {
        "symbol": symbol,
        "side": side,
        "type": order_type,
        "quantity": quantity,
    }
    if order_type == "LIMIT":
        payload["price"] = price
        payload["timeInForce"] = time_in_force
    return payload


def place_order(
    client: BinanceClient,
    symbol: str,
    side: str,
    order_type: str,
    quantity: float | str,
    price: float | str | None = None,
    time_in_force: str = DEFAULT_TIME_IN_FORCE,
) -> dict:
    """
    Validate parameters, place the order, and return the API response dict.

    Raises:
        validators.ValidationError  – bad input
        client.BinanceAPIError      – Binance rejected the order
        requests.RequestException   – network-level failure
    """
    cleaned = validate_order_params(symbol, side, order_type, quantity, price)

    logger.info(
        "Placing %s %s order: symbol=%s qty=%s price=%s",
        cleaned["side"],
        cleaned["order_type"],
        cleaned["symbol"],
        cleaned["quantity"],
        cleaned["price"],
    )

    payload = _build_order_payload(
        symbol=cleaned["symbol"],
        side=cleaned["side"],
        order_type=cleaned["order_type"],
        quantity=cleaned["quantity"],
        price=cleaned["price"],
        time_in_force=time_in_force,
    )

    response = client.place_order(**payload)
    return response


_STATUS_STYLES: dict[str, str] = {
    "FILLED": "bold green",
    "NEW": "bold yellow",
    "PARTIALLY_FILLED": "yellow",
    "CANCELED": "bold red",
    "REJECTED": "bold red",
    "EXPIRED": "dim",
}


def print_request_summary(
    symbol: str,
    side: str,
    order_type: str,
    quantity: float,
    price: float | None,
    time_in_force: str,
    console: Console,
) -> None:
    """Print a styled summary of the order about to be placed."""
    table = Table(show_header=False, box=None, padding=(0, 2))
    table.add_column(style="dim", no_wrap=True)
    table.add_column()

    side_style = "bold green" if side == "BUY" else "bold red"

    table.add_row("Symbol", symbol)
    table.add_row("Side", Text(side, style=side_style))
    table.add_row("Type", order_type)
    table.add_row("Quantity", str(quantity))
    if order_type == "LIMIT":
        table.add_row("Price", str(price))
        table.add_row("Time-in-Force", time_in_force)

    console.print(Panel(table, title="[bold]Submitting Order[/bold]", border_style="blue"))


def print_order_summary(response: dict, console: Console) -> None:
    """Print a styled summary of the order response."""
    status = response.get("status", "N/A")
    status_style = _STATUS_STYLES.get(status, "white")

    table = Table(show_header=False, box=None, padding=(0, 2))
    table.add_column(style="dim", no_wrap=True)
    table.add_column()

    table.add_row("Order ID", str(response.get("orderId", "N/A")))
    table.add_row("Symbol", str(response.get("symbol", "N/A")))
    side = response.get("side", "N/A")
    side_style = "bold green" if side == "BUY" else "bold red"
    table.add_row("Side", Text(side, style=side_style))
    table.add_row("Type", str(response.get("type", "N/A")))
    table.add_row("Status", Text(status, style=status_style))
    table.add_row("Orig Qty", str(response.get("origQty", "N/A")))
    table.add_row("Executed Qty", str(response.get("executedQty", "N/A")))
    table.add_row("Avg Price", str(response.get("avgPrice", "N/A")))
    table.add_row("Limit Price", str(response.get("price", "N/A")))
    table.add_row("Update Time", str(response.get("updateTime", "N/A")))

    border = "green" if status == "FILLED" else "yellow" if status == "NEW" else "red"
    console.print(Panel(table, title="[bold]Order Result[/bold]", border_style=border))
