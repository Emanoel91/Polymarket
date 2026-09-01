"""
Polymarket CLOB API client.

Base URL:
https://clob.polymarket.com

Read-only functionality:
- Order books
- Prices
- Midpoints
- Spreads
- Last trade prices
- Price history
- Fee rates
- Tick sizes
- Market information
- Rewards
"""

from __future__ import annotations

import time
from typing import Any, Dict, List, Optional

import requests


class CLOBAPI:
    """Read-only Polymarket CLOB API client."""

    BASE_URL = "https://clob.polymarket.com"

    def __init__(
        self,
        timeout: int = 30,
        max_retries: int = 3,
        backoff_factor: float = 0.5,
    ):
        self.timeout = timeout
        self.max_retries = max_retries
        self.backoff_factor = backoff_factor

        self.session = requests.Session()

        self.session.headers.update(
            {
                "Accept": "application/json",
                "User-Agent": "Polymarket-Streamlit-Dashboard/1.0",
            }
        )

    # ------------------------------------------------------------------
    # HTTP helper
    # ------------------------------------------------------------------

    def _request(
        self,
        method: str,
        endpoint: str,
        params: Optional[Dict[str, Any]] = None,
        json: Optional[Any] = None,
    ) -> Any:

        url = f"{self.BASE_URL}{endpoint}"

        for attempt in range(self.max_retries):

            try:

                response = self.session.request(
                    method=method,
                    url=url,
                    params=params,
                    json=json,
                    timeout=self.timeout,
                )

                if response.status_code in {
                    429,
                    500,
                    502,
                    503,
                    504,
                }:

                    if attempt < self.max_retries - 1:
                        time.sleep(
                            self.backoff_factor * (2**attempt)
                        )
                        continue

                response.raise_for_status()

                return response.json()

            except requests.RequestException as exc:

                if attempt < self.max_retries - 1:
                    time.sleep(
                        self.backoff_factor * (2**attempt)
                    )
                    continue

                raise RuntimeError(
                    f"CLOB API request failed: "
                    f"{method} {url}"
                ) from exc

        raise RuntimeError(
            f"CLOB API request failed: {method} {url}"
        )

    # ------------------------------------------------------------------
    # Order Book
    # ------------------------------------------------------------------

    def get_order_book(
        self,
        token_id: str,
    ) -> Dict[str, Any]:

        return self._request(
            "GET",
            "/book",
            params={
                "token_id": token_id,
            },
        )

    def get_order_books(
        self,
        token_ids: List[str],
    ) -> Any:

        body = [
            {
                "token_id": token_id,
            }
            for token_id in token_ids
        ]

        return self._request(
            "POST",
            "/books",
            json=body,
        )

    # ------------------------------------------------------------------
    # Prices
    # ------------------------------------------------------------------

    def get_price(
        self,
        token_id: str,
        side: str = "BUY",
    ) -> Any:

        side = side.upper()

        if side not in {"BUY", "SELL"}:
            raise ValueError(
                "side must be either BUY or SELL"
            )

        return self._request(
            "GET",
            "/price",
            params={
                "token_id": token_id,
                "side": side,
            },
        )

    def get_prices(
        self,
        params: Dict[str, Any],
    ) -> Any:

        return self._request(
            "GET",
            "/prices",
            params=params,
        )

    def get_prices_batch(
        self,
        requests_body: List[Dict[str, Any]],
    ) -> Any:

        return self._request(
            "POST",
            "/prices",
            json=requests_body,
        )

    # ------------------------------------------------------------------
    # Midpoint
    # ------------------------------------------------------------------

    def get_midpoint(
        self,
        token_id: str,
    ) -> Any:

        return self._request(
            "GET",
            "/midpoint",
            params={
                "token_id": token_id,
            },
        )

    def get_midpoints(
        self,
        params: Optional[Dict[str, Any]] = None,
    ) -> Any:

        return self._request(
            "GET",
            "/midpoints",
            params=params,
        )

    def get_midpoints_batch(
        self,
        requests_body: List[Dict[str, Any]],
    ) -> Any:

        return self._request(
            "POST",
            "/midpoints",
            json=requests_body,
        )

    # ------------------------------------------------------------------
    # Spread
    # ------------------------------------------------------------------

    def get_spread(
        self,
        token_id: str,
    ) -> Any:

        return self._request(
            "GET",
            "/spread",
            params={
                "token_id": token_id,
            },
        )

    def get_spreads(
        self,
        params: Optional[Dict[str, Any]] = None,
    ) -> Any:

        return self._request(
            "GET",
            "/spreads",
            params=params,
        )

    # ------------------------------------------------------------------
    # Last Trade Price
    # ------------------------------------------------------------------

    def get_last_trade_price(
        self,
        token_id: str,
    ) -> Any:

        return self._request(
            "GET",
            "/last-trade-price",
            params={
                "token_id": token_id,
            },
        )

    def get_last_trade_prices(
        self,
        params: Optional[Dict[str, Any]] = None,
    ) -> Any:

        return self._request(
            "GET",
            "/last-trades-prices",
            params=params,
        )

    def get_last_trade_prices_batch(
        self,
        requests_body: List[Dict[str, Any]],
    ) -> Any:

        return self._request(
            "POST",
            "/last-trades-prices",
            json=requests_body,
        )

    # ------------------------------------------------------------------
    # Price History
    # ------------------------------------------------------------------

    def get_price_history(
        self,
        token_id: str,
        interval: Optional[str] = None,
        fidelity: Optional[int] = None,
        start_ts: Optional[int] = None,
        end_ts: Optional[int] = None,
    ) -> Any:

        params = {
            "market": token_id,
        }

        if interval:
            params["interval"] = interval

        if fidelity is not None:
            params["fidelity"] = fidelity

        if start_ts is not None:
            params["startTs"] = start_ts

        if end_ts is not None:
            params["endTs"] = end_ts

        return self._request(
            "GET",
            "/prices-history",
            params=params,
        )

    # ------------------------------------------------------------------
    # Market information
    # ------------------------------------------------------------------

    def get_market(
        self,
        condition_id: str,
    ) -> Any:

        return self._request(
            "GET",
            f"/markets/{condition_id}",
        )

    def get_fee_rate(
        self,
        token_id: str,
    ) -> Any:

        return self._request(
            "GET",
            "/fee-rate",
            params={
                "token_id": token_id,
            },
        )

    def get_tick_size(
        self,
        token_id: str,
    ) -> Any:

        return self._request(
            "GET",
            "/tick-size",
            params={
                "token_id": token_id,
            },
        )

    def get_server_time(self) -> Any:

        return self._request(
            "GET",
            "/time",
        )

    # ------------------------------------------------------------------
    # Rewards
    # ------------------------------------------------------------------

    def get_rewards_markets(
        self,
        **params,
    ) -> Any:

        return self._request(
            "GET",
            "/rewards/markets",
            params=params or None,
        )

    def get_market_rewards(
        self,
        condition_id: str,
    ) -> Any:

        return self._request(
            "GET",
            f"/rewards/markets/{condition_id}",
        )


CLOBClient = CLOBAPI
