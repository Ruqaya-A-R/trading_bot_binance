"""Input validation for order parameters."""

from __future__ import annotations

VALID_SIDES = {"BUY", "SELL"}
VALID_ORDER_TYPES = {"MARKET", "LIMIT"}


class ValidationError(ValueError):
    """Raised when order parameters fail validation."""


def validate_symbol(symbol: str) -> str:
    s = symbol.strip().upper()
    if not s or not s.isalnum():
        raise ValidationError(
            f"Invalid symbol '{symbol}'. Must be alphanumeric (e.g. BTCUSDT)."
        )
    return s


def validate_side(side: str) -> str:
    s = side.strip().upper()
    if s not in VALID_SIDES:
        raise ValidationError(
            f"Invalid side '{side}'. Must be one of: {', '.join(sorted(VALID_SIDES))}."
        )
    return s


def validate_order_type(order_type: str) -> str:
    t = order_type.strip().upper()
    if t not in VALID_ORDER_TYPES:
        raise ValidationError(
            f"Invalid order type '{order_type}'. Must be one of: {', '.join(sorted(VALID_ORDER_TYPES))}."
        )
    return t


def validate_quantity(quantity: float | str) -> float:
    try:
        qty = float(quantity)
    except (TypeError, ValueError):
        raise ValidationError(f"Invalid quantity '{quantity}'. Must be a positive number.")
    if qty <= 0:
        raise ValidationError(f"Quantity must be greater than 0, got {qty}.")
    return qty


def validate_price(price: float | str | None, order_type: str) -> float | None:
    if order_type == "MARKET":
        if price is not None:
            raise ValidationError(
                "MARKET orders do not use a price. Remove --price or switch to --order-type LIMIT."
            )
        return None

    # LIMIT order
    if price is None:
        raise ValidationError("Price is required for LIMIT orders.")
    try:
        p = float(price)
    except (TypeError, ValueError):
        raise ValidationError(f"Invalid price '{price}'. Must be a positive number.")
    if p <= 0:
        raise ValidationError(f"Price must be greater than 0, got {p}.")
    return p


def validate_order_params(
    symbol: str,
    side: str,
    order_type: str,
    quantity: float | str,
    price: float | str | None = None,
) -> dict:
    """Validate all order parameters and return a cleaned dict."""
    cleaned_type = validate_order_type(order_type)
    return {
        "symbol": validate_symbol(symbol),
        "side": validate_side(side),
        "order_type": cleaned_type,
        "quantity": validate_quantity(quantity),
        "price": validate_price(price, cleaned_type),
    }
