"""
Polymarket Data API client.

Base URL:
https://data-api.polymarket.com

Read-only functionality:
- Profiles
- Positions
- Closed positions
- Activity
- Wallet value
- Trades
- Leaderboard
- Open interest
- Builder analytics
"""

from __future__ import annotations

import time
from typing import Any, Dict, Optional

import requests


class DataAPI:
    """Read-only client for Polymarket Data API."""

    BASE_URL = "https://data-api.polymarket.com"

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
    ) -> Any:

        url = f"{self.BASE_URL}{endpoint}"

        for attempt in range(self.max_retries):

            try:

                response = self.session.request(
                    method=method,
                    url=url,
                    params=params,
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
                    f"Data API request failed: "
                    f"{method} {url}"
                ) from exc

        raise RuntimeError(
            f"Data API request failed: {method} {url}"
        )

    # ------------------------------------------------------------------
    # Profile
    # ------------------------------------------------------------------

    def get_profile(
        self,
        wallet: str,
    ) -> Any:

        return self._request(
            "GET",
            "/profile",
            params={
                "address": wallet,
            },
        )

    # ------------------------------------------------------------------
    # Positions
    # ------------------------------------------------------------------

    def get_positions(
        self,
        wallet: str,
        **params,
    ) -> Any:

        params["user"] = wallet

        return self._request(
            "GET",
            "/positions",
            params=params,
        )

    def get_closed_positions(
        self,
        wallet: str,
        **params,
    ) -> Any:

        params["user"] = wallet

        return self._request(
            "GET",
            "/positions/closed",
            params=params,
        )

    # ------------------------------------------------------------------
    # Activity
    # ------------------------------------------------------------------

    def get_activity(
        self,
        wallet: str,
        limit: int = 100,
        offset: int = 0,
        start: Optional[int] = None,
        end: Optional[int] = None,
        activity_type: Optional[str] = None,
        sort_by: str = "TIMESTAMP",
        sort_direction: str = "DESC",
    ) -> Any:

        params = {
            "user": wallet,
            "limit": limit,
            "offset": offset,
            "sortBy": sort_by,
            "sortDirection": sort_direction,
        }

        if start is not None:
            params["start"] = start

        if end is not None:
            params["end"] = end

        if activity_type:
            params["type"] = activity_type

        return self._request(
            "GET",
            "/activity",
            params=params,
        )

    # ------------------------------------------------------------------
    # Portfolio Value
    # ------------------------------------------------------------------

    def get_value(
        self,
        wallet: str,
    ) -> Any:

        return self._request(
            "GET",
            "/value",
            params={
                "user": wallet,
            },
        )

    # ------------------------------------------------------------------
    # Trades
    # ------------------------------------------------------------------

    def get_trades(
        self,
        wallet: Optional[str] = None,
        market: Optional[str] = None,
        limit: int = 100,
        offset: int = 0,
        **filters,
    ) -> Any:

        params = {
            "limit": limit,
            "offset": offset,
            **filters,
        }

        if wallet:
            params["user"] = wallet

        if market:
            params["market"] = market

        return self._request(
            "GET",
            "/trades",
            params=params,
        )

    # ------------------------------------------------------------------
    # Leaderboard
    # ------------------------------------------------------------------

    def get_leaderboard(
        self,
        window: str = "day",
        **params,
    ) -> Any:

        params["window"] = window

        return self._request(
            "GET",
            "/leaderboard",
            params=params,
        )

    # ------------------------------------------------------------------
    # Open Interest
    # ------------------------------------------------------------------

    def get_open_interest(
        self,
        **params,
    ) -> Any:

        return self._request(
            "GET",
            "/oi",
            params=params or None,
        )

    # ------------------------------------------------------------------
    # Builder Leaderboard
    # ------------------------------------------------------------------

    def get_builder_leaderboard(
        self,
        **params,
    ) -> Any:

        return self._request(
            "GET",
            "/builders/leaderboard",
            params=params or None,
        )

    # ------------------------------------------------------------------
    # Builder Volume
    # ------------------------------------------------------------------

    def get_builder_volume(
        self,
        **params,
    ) -> Any:

        return self._request(
            "GET",
            "/builders/volume",
            params=params or None,
        )

    # ------------------------------------------------------------------
    # Accounting Snapshot
    # ------------------------------------------------------------------

    def get_accounting_snapshot(
        self,
        wallet: str,
    ) -> Any:

        return self._request(
            "GET",
            "/accounting-snapshot",
            params={
                "user": wallet,
            },
        )
