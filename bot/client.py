"""Binance Futures Testnet API client with HMAC-SHA256 authentication."""

from __future__ import annotations

import hashlib
import hmac
import time
import urllib.parse
from typing import Any

import requests

from bot.logging_config import get_logger

BASE_URL = "https://testnet.binancefuture.com"
RECV_WINDOW = 5000  # milliseconds

logger = get_logger("client")


class BinanceAPIError(Exception):
    """Raised when Binance returns a non-2xx response or an error payload."""

    def __init__(self, code: int, message: str) -> None:
        self.code = code
        self.message = message
        super().__init__(f"Binance API error {code}: {message}")


class BinanceClient:
    def __init__(self, api_key: str, api_secret: str, timeout: int = 10) -> None:
        if not api_key or not api_secret:
            raise ValueError("api_key and api_secret must not be empty.")
        self._api_key = api_key
        self._api_secret = api_secret.encode()
        self._timeout = timeout
        self._session = requests.Session()
        self._session.headers.update(
            {
                "X-MBX-APIKEY": api_key,
                "Content-Type": "application/x-www-form-urlencoded",
            }
        )

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _timestamp(self) -> int:
        return int(time.time() * 1000)

    def _sign(self, params: dict) -> str:
        query = urllib.parse.urlencode(params)
        return hmac.new(self._api_secret, query.encode(), hashlib.sha256).hexdigest()

    def _signed_params(self, params: dict) -> dict:
        params["timestamp"] = self._timestamp()
        params["recvWindow"] = RECV_WINDOW
        params["signature"] = self._sign(params)
        return params

    def _handle_response(self, response: requests.Response) -> Any:
        logger.debug("Response [%s] %s: %s", response.status_code, response.url, response.text)

        try:
            data = response.json()
        except ValueError:
            response.raise_for_status()
            return response.text

        if isinstance(data, dict) and data.get("code", 0) < 0:
            raise BinanceAPIError(data["code"], data.get("msg", "Unknown error"))

        response.raise_for_status()
        return data

    # ------------------------------------------------------------------
    # Public API methods
    # ------------------------------------------------------------------

    def get_exchange_info(self) -> dict:
        """Fetch exchange info (no auth required)."""
        url = f"{BASE_URL}/fapi/v1/exchangeInfo"
        logger.debug("GET %s", url)
        resp = self._session.get(url, timeout=self._timeout)
        return self._handle_response(resp)

    def get_account(self) -> dict:
        """Fetch account information."""
        url = f"{BASE_URL}/fapi/v2/account"
        params = self._signed_params({})
        logger.debug("GET %s params=%s", url, {k: v for k, v in params.items() if k != "signature"})
        resp = self._session.get(url, params=params, timeout=self._timeout)
        return self._handle_response(resp)

    def place_order(self, **order_params) -> dict:
        """
        Place an order on Binance Futures Testnet.

        Required keys: symbol, side, type, quantity.
        Optional keys: price (for LIMIT), timeInForce (for LIMIT), etc.
        """
        url = f"{BASE_URL}/fapi/v1/order"
        params = self._signed_params(dict(order_params))

        loggable = {k: v for k, v in params.items() if k != "signature"}
        logger.info("POST %s params=%s", url, loggable)

        resp = self._session.post(url, data=params, timeout=self._timeout)
        data = self._handle_response(resp)
        logger.info("Order response: %s", data)
        return data

    def cancel_order(self, symbol: str, order_id: int) -> dict:
        """Cancel an open order."""
        url = f"{BASE_URL}/fapi/v1/order"
        params = self._signed_params({"symbol": symbol, "orderId": order_id})
        logger.info("DELETE %s orderId=%s", url, order_id)
        resp = self._session.delete(url, params=params, timeout=self._timeout)
        data = self._handle_response(resp)
        logger.info("Cancel response: %s", data)
        return data

    def get_order(self, symbol: str, order_id: int) -> dict:
        """Query a single order."""
        url = f"{BASE_URL}/fapi/v1/order"
        params = self._signed_params({"symbol": symbol, "orderId": order_id})
        logger.debug("GET %s orderId=%s", url, order_id)
        resp = self._session.get(url, params=params, timeout=self._timeout)
        return self._handle_response(resp)
