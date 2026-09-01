"""
Polymarket WebSocket client.

Public market stream:
wss://ws-subscriptions-clob.polymarket.com/ws/market

This client is intended for read-only dashboard use.
"""

from __future__ import annotations

import json
import threading
from typing import Callable, List, Optional

import websocket


class PolymarketWebSocket:
    """
    WebSocket client for Polymarket market data.

    Example
    -------
    ws = PolymarketWebSocket(
        asset_ids=["TOKEN_ID"]
    )

    ws.start()
    """

    MARKET_URL = (
        "wss://ws-subscriptions-clob.polymarket.com/ws/market"
    )

    SPORTS_URL = (
        "wss://ws-subscriptions-clob.polymarket.com/ws/sports"
    )

    def __init__(
        self,
        asset_ids: Optional[List[str]] = None,
        url: Optional[str] = None,
        on_message: Optional[Callable] = None,
        on_error: Optional[Callable] = None,
        on_close: Optional[Callable] = None,
        on_open: Optional[Callable] = None,
    ):

        self.asset_ids = asset_ids or []

        self.url = url or self.MARKET_URL

        self.on_message_callback = on_message
        self.on_error_callback = on_error
        self.on_close_callback = on_close
        self.on_open_callback = on_open

        self.ws: Optional[websocket.WebSocketApp] = None
        self.thread: Optional[threading.Thread] = None

    # ------------------------------------------------------------------
    # Subscription
    # ------------------------------------------------------------------

    def _subscription_message(self) -> dict:

        return {
            "assets_ids": self.asset_ids,
            "type": "market",
        }

    # ------------------------------------------------------------------
    # Callbacks
    # ------------------------------------------------------------------

    def _on_open(self, ws):

        message = self._subscription_message()

        ws.send(
            json.dumps(message)
        )

        if self.on_open_callback:
            self.on_open_callback(ws)

    def _on_message(self, ws, message):

        try:
            parsed = json.loads(message)
        except json.JSONDecodeError:
            parsed = message

        if self.on_message_callback:
            self.on_message_callback(parsed)

    def _on_error(self, ws, error):

        if self.on_error_callback:
            self.on_error_callback(error)

    def _on_close(
        self,
        ws,
        close_status_code,
        close_msg,
    ):

        if self.on_close_callback:
            self.on_close_callback(
                close_status_code,
                close_msg,
            )

    # ------------------------------------------------------------------
    # Start
    # ------------------------------------------------------------------

    def start(
        self,
        daemon: bool = True,
        reconnect: bool = False,
    ):

        self.ws = websocket.WebSocketApp(
            self.url,
            on_open=self._on_open,
            on_message=self._on_message,
            on_error=self._on_error,
            on_close=self._on_close,
        )

        if reconnect:

            self.thread = threading.Thread(
                target=self._run_forever_with_reconnect,
                daemon=daemon,
            )

        else:

            self.thread = threading.Thread(
                target=self.ws.run_forever,
                daemon=daemon,
            )

        self.thread.start()

        return self.thread

    # ------------------------------------------------------------------
    # Reconnection
    # ------------------------------------------------------------------

    def _run_forever_with_reconnect(self):

        while True:

            try:

                self.ws.run_forever()

            except Exception:
                pass

    # ------------------------------------------------------------------
    # Stop
    # ------------------------------------------------------------------

    def stop(self):

        if self.ws:

            self.ws.close()

        self.ws = None

    # ------------------------------------------------------------------
    # Update subscription
    # ------------------------------------------------------------------

    def update_assets(
        self,
        asset_ids: List[str],
    ):

        self.asset_ids = asset_ids

        if self.ws:

            message = self._subscription_message()

            self.ws.send(
                json.dumps(message)
            )
