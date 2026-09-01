"""
Gamma API client for Polymarket.

Base URL:
https://gamma-api.polymarket.com

This module provides read-only helpers for:
- Events
- Markets
- Tags
- Series
- Comments
- Search
- Sports metadata
- Teams
"""

from __future__ import annotations

import time
from typing import Any, Dict, Iterator, List, Optional

import requests


class GammaAPI:
    """Read-only client for the Polymarket Gamma API."""

    BASE_URL = "https://gamma-api.polymarket.com"

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
    # Internal HTTP helper
    # ------------------------------------------------------------------

    def _request(
        self,
        method: str,
        endpoint: str,
        params: Optional[Dict[str, Any]] = None,
    ) -> Any:

        url = f"{self.BASE_URL}{endpoint}"

        last_exception = None

        for attempt in range(self.max_retries):

            try:
                response = self.session.request(
                    method=method,
                    url=url,
                    params=params,
                    timeout=self.timeout,
                )

                # Retry temporary server/rate-limit errors
                if response.status_code in {429, 500, 502, 503, 504}:

                    if attempt < self.max_retries - 1:
                        sleep_time = self.backoff_factor * (2**attempt)
                        time.sleep(sleep_time)
                        continue

                response.raise_for_status()

                return response.json()

            except requests.RequestException as exc:

                last_exception = exc

                if attempt < self.max_retries - 1:
                    sleep_time = self.backoff_factor * (2**attempt)
                    time.sleep(sleep_time)
                else:
                    raise RuntimeError(
                        f"Gamma API request failed: {method} {url}"
                    ) from exc

        raise RuntimeError(
            f"Gamma API request failed: {method} {url}"
        ) from last_exception

    # ------------------------------------------------------------------
    # Events
    # ------------------------------------------------------------------

    def get_events(
        self,
        limit: int = 100,
        offset: int = 0,
        **filters,
    ) -> List[Dict[str, Any]]:
        """
        Get events using offset pagination.

        Example
        -------
        events = gamma.get_events(
            active=True,
            closed=False,
            limit=100
        )
        """

        params = {
            "limit": limit,
            "offset": offset,
            **filters,
        }

        return self._request(
            "GET",
            "/events",
            params=params,
        )

    def get_event(
        self,
        event_id: str | int,
    ) -> Dict[str, Any]:

        return self._request(
            "GET",
            f"/events/{event_id}",
        )

    def get_event_by_slug(
        self,
        slug: str,
    ) -> Dict[str, Any]:

        return self._request(
            "GET",
            f"/events/slug/{slug}",
        )

    def get_event_tags(
        self,
        event_id: str | int,
    ) -> Any:

        return self._request(
            "GET",
            f"/events/{event_id}/tags",
        )

    # ------------------------------------------------------------------
    # Events - Keyset pagination
    # ------------------------------------------------------------------

    def get_events_keyset(
        self,
        limit: int = 100,
        after_cursor: Optional[str] = None,
        **filters,
    ) -> Dict[str, Any]:

        params = {
            "limit": limit,
            **filters,
        }

        if after_cursor:
            params["after_cursor"] = after_cursor

        return self._request(
            "GET",
            "/events/keyset",
            params=params,
        )

    def iter_events(
        self,
        limit: int = 100,
        **filters,
    ) -> Iterator[Dict[str, Any]]:
        """
        Iterate through all events using keyset pagination.
        """

        cursor = None

        while True:

            response = self.get_events_keyset(
                limit=limit,
                after_cursor=cursor,
                **filters,
            )

            if isinstance(response, list):
                for event in response:
                    yield event

                break

            items = (
                response.get("data")
                or response.get("events")
                or response.get("items")
                or []
            )

            for event in items:
                yield event

            cursor = response.get("next_cursor")

            if not cursor:
                break

    # ------------------------------------------------------------------
    # Markets
    # ------------------------------------------------------------------

    def get_markets(
        self,
        limit: int = 100,
        offset: int = 0,
        **filters,
    ) -> List[Dict[str, Any]]:

        params = {
            "limit": limit,
            "offset": offset,
            **filters,
        }

        return self._request(
            "GET",
            "/markets",
            params=params,
        )

    def get_market(
        self,
        market_id: str | int,
    ) -> Dict[str, Any]:

        return self._request(
            "GET",
            f"/markets/{market_id}",
        )

    def get_market_by_slug(
        self,
        slug: str,
    ) -> Dict[str, Any]:

        return self._request(
            "GET",
            f"/markets/slug/{slug}",
        )

    def get_market_by_token(
        self,
        token_id: str,
    ) -> Dict[str, Any]:

        return self._request(
            "GET",
            f"/markets/token/{token_id}",
        )

    def get_market_tags(
        self,
        market_id: str | int,
    ) -> Any:

        return self._request(
            "GET",
            f"/markets/{market_id}/tags",
        )

    # ------------------------------------------------------------------
    # Markets - Keyset
    # ------------------------------------------------------------------

    def get_markets_keyset(
        self,
        limit: int = 100,
        after_cursor: Optional[str] = None,
        **filters,
    ) -> Dict[str, Any]:

        params = {
            "limit": limit,
            **filters,
        }

        if after_cursor:
            params["after_cursor"] = after_cursor

        return self._request(
            "GET",
            "/markets/keyset",
            params=params,
        )

    def iter_markets(
        self,
        limit: int = 100,
        **filters,
    ) -> Iterator[Dict[str, Any]]:
        """
        Iterate through all markets using keyset pagination.
        """

        cursor = None

        while True:

            response = self.get_markets_keyset(
                limit=limit,
                after_cursor=cursor,
                **filters,
            )

            if isinstance(response, list):
                for market in response:
                    yield market

                break

            items = (
                response.get("data")
                or response.get("markets")
                or response.get("items")
                or []
            )

            for market in items:
                yield market

            cursor = response.get("next_cursor")

            if not cursor:
                break

    # ------------------------------------------------------------------
    # Simplified markets
    # ------------------------------------------------------------------

    def get_simplified_markets(
        self,
        limit: int = 100,
        offset: int = 0,
        **filters,
    ) -> Any:

        params = {
            "limit": limit,
            "offset": offset,
            **filters,
        }

        return self._request(
            "GET",
            "/markets/simplified",
            params=params,
        )

    # ------------------------------------------------------------------
    # Tags
    # ------------------------------------------------------------------

    def get_tags(
        self,
        limit: int = 100,
        offset: int = 0,
    ) -> Any:

        return self._request(
            "GET",
            "/tags",
            params={
                "limit": limit,
                "offset": offset,
            },
        )

    def get_tag(
        self,
        tag_id: str | int,
    ) -> Any:

        return self._request(
            "GET",
            f"/tags/{tag_id}",
        )

    def get_tag_by_slug(
        self,
        slug: str,
    ) -> Any:

        return self._request(
            "GET",
            f"/tags/slug/{slug}",
        )

    def get_related_tags(
        self,
        tag_id: str | int,
    ) -> Any:

        return self._request(
            "GET",
            f"/tags/{tag_id}/related-tags",
        )

    # ------------------------------------------------------------------
    # Series
    # ------------------------------------------------------------------

    def get_series(
        self,
        limit: int = 100,
        offset: int = 0,
        **filters,
    ) -> Any:

        return self._request(
            "GET",
            "/series",
            params={
                "limit": limit,
                "offset": offset,
                **filters,
            },
        )

    def get_series_by_id(
        self,
        series_id: str | int,
    ) -> Any:

        return self._request(
            "GET",
            f"/series/{series_id}",
        )

    # ------------------------------------------------------------------
    # Comments
    # ------------------------------------------------------------------

    def get_comments(
        self,
        limit: int = 100,
        offset: int = 0,
        **filters,
    ) -> Any:

        return self._request(
            "GET",
            "/comments",
            params={
                "limit": limit,
                "offset": offset,
                **filters,
            },
        )

    def get_comment(
        self,
        comment_id: str | int,
    ) -> Any:

        return self._request(
            "GET",
            f"/comments/{comment_id}",
        )

    def get_user_comments(
        self,
        address: str,
        limit: int = 100,
        offset: int = 0,
    ) -> Any:

        return self._request(
            "GET",
            f"/comments/user/{address}",
            params={
                "limit": limit,
                "offset": offset,
            },
        )

    # ------------------------------------------------------------------
    # Search
    # ------------------------------------------------------------------

    def search(
        self,
        query: str,
        **params,
    ) -> Any:

        params["q"] = query

        return self._request(
            "GET",
            "/public-search",
            params=params,
        )

    # ------------------------------------------------------------------
    # Sports
    # ------------------------------------------------------------------

    def get_sports(self) -> Any:

        return self._request(
            "GET",
            "/sports",
        )

    def get_sports_market_types(self) -> Any:

        return self._request(
            "GET",
            "/sports/market-types",
        )

    def get_teams(self) -> Any:

        return self._request(
            "GET",
            "/teams",
        )
