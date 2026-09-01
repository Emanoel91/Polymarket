"""
Polymarket Gamma API Client

Base URL:
    https://gamma-api.polymarket.com

Features:
- Robust HTTP error handling
- Retry for transient errors
- Detailed API error messages
- Events pagination
- Markets pagination
- Offset-based pagination
- Automatic response normalization
- Support for common Gamma endpoints
"""

from __future__ import annotations

import time
from typing import Any, Dict, List, Optional

import requests


class GammaAPIError(Exception):
    """Custom exception for Gamma API errors."""

    def __init__(
        self,
        message: str,
        *,
        status_code: Optional[int] = None,
        url: Optional[str] = None,
        response_text: Optional[str] = None,
    ):
        super().__init__(message)

        self.status_code = status_code
        self.url = url
        self.response_text = response_text


class GammaClient:
    """Client for Polymarket Gamma API."""

    BASE_URL = "https://gamma-api.polymarket.com"

    def __init__(
        self,
        base_url: Optional[str] = None,
        timeout: int = 30,
        max_retries: int = 3,
        backoff_factor: float = 1.5,
    ):
        self.base_url = (base_url or self.BASE_URL).rstrip("/")
        self.timeout = timeout
        self.max_retries = max_retries
        self.backoff_factor = backoff_factor

        self.session = requests.Session()

        # Browser-like headers help avoid unnecessary proxy/CDN issues.
        self.session.headers.update(
            {
                "Accept": "application/json",
                "User-Agent": (
                    "Mozilla/5.0 "
                    "(Windows NT 10.0; Win64; x64) "
                    "AppleWebKit/537.36 "
                    "(KHTML, like Gecko) "
                    "Chrome/151.0.0.0 Safari/537.36"
                ),
            }
        )

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _build_url(self, endpoint: str) -> str:
        """Build a complete API URL."""

        if endpoint.startswith("http://") or endpoint.startswith("https://"):
            return endpoint

        endpoint = endpoint.lstrip("/")

        return f"{self.base_url}/{endpoint}"

    @staticmethod
    def _extract_error_text(response: requests.Response) -> str:
        """
        Extract useful error information from an API response.
        """

        try:
            data = response.json()

            if isinstance(data, dict):
                for key in (
                    "error",
                    "message",
                    "detail",
                    "description",
                ):
                    if data.get(key):
                        return str(data[key])

                return str(data)

            return str(data)

        except ValueError:
            text = response.text.strip()

            if text:
                return text[:2000]

            return "<empty response body>"

    @staticmethod
    def _normalize_list_response(data: Any) -> List[Dict[str, Any]]:
        """
        Normalize Gamma list responses.

        Expected response:
            [
                {...},
                {...}
            ]

        But this also supports possible wrapper formats such as:
            {"data": [...]}
            {"events": [...]}
            {"markets": [...]}
            {"results": [...]}
        """

        if data is None:
            return []

        if isinstance(data, list):
            return data

        if isinstance(data, dict):

            possible_keys = (
                "data",
                "events",
                "markets",
                "results",
                "items",
            )

            for key in possible_keys:
                value = data.get(key)

                if isinstance(value, list):
                    return value

        raise GammaAPIError(
            "Unexpected Gamma API response format. "
            f"Expected a list but received: {type(data).__name__}"
        )

    # ------------------------------------------------------------------
    # Generic GET
    # ------------------------------------------------------------------

    def get(
        self,
        endpoint: str,
        params: Optional[Dict[str, Any]] = None,
    ) -> Any:
        """
        Perform a GET request with retries and detailed error handling.
        """

        url = self._build_url(endpoint)

        last_exception = None

        for attempt in range(self.max_retries + 1):

            try:

                response = self.session.get(
                    url,
                    params=params,
                    timeout=self.timeout,
                )

                # ------------------------------------------------------
                # Successful response
                # ------------------------------------------------------

                if response.ok:

                    try:
                        return response.json()

                    except ValueError as exc:

                        raise GammaAPIError(
                            "Gamma API returned a non-JSON response.\n"
                            f"Endpoint: GET {response.url}\n"
                            f"Status: {response.status_code}\n"
                            f"Response: {response.text[:2000]}"
                        ) from exc

                # ------------------------------------------------------
                # Retryable HTTP errors
                # ------------------------------------------------------

                if response.status_code in (429, 500, 502, 503, 504):

                    if attempt < self.max_retries:

                        retry_after = response.headers.get("Retry-After")

                        if retry_after:

                            try:
                                sleep_seconds = float(retry_after)

                            except ValueError:
                                sleep_seconds = (
                                    self.backoff_factor
                                    * (2 ** attempt)
                                )

                        else:
                            sleep_seconds = (
                                self.backoff_factor
                                * (2 ** attempt)
                            )

                        time.sleep(sleep_seconds)

                        continue

                # ------------------------------------------------------
                # Non-retryable error
                # ------------------------------------------------------

                error_text = self._extract_error_text(response)

                raise GammaAPIError(
                    "Gamma API request failed.\n"
                    f"Endpoint: GET {response.url}\n"
                    f"Status: {response.status_code}\n"
                    f"Response: {error_text}",
                    status_code=response.status_code,
                    url=response.url,
                    response_text=error_text,
                )

            except requests.exceptions.Timeout as exc:

                last_exception = exc

                if attempt < self.max_retries:

                    sleep_seconds = (
                        self.backoff_factor
                        * (2 ** attempt)
                    )

                    time.sleep(sleep_seconds)

                    continue

                raise GammaAPIError(
                    "Gamma API request timed out.\n"
                    f"Endpoint: GET {url}\n"
                    f"Timeout: {self.timeout} seconds"
                ) from exc

            except requests.exceptions.ConnectionError as exc:

                last_exception = exc

                if attempt < self.max_retries:

                    sleep_seconds = (
                        self.backoff_factor
                        * (2 ** attempt)
                    )

                    time.sleep(sleep_seconds)

                    continue

                raise GammaAPIError(
                    "Could not connect to Gamma API.\n"
                    f"Endpoint: GET {url}\n"
                    f"Error: {str(exc)}"
                ) from exc

            except requests.exceptions.RequestException as exc:

                raise GammaAPIError(
                    "Unexpected HTTP request error.\n"
                    f"Endpoint: GET {url}\n"
                    f"Error: {str(exc)}"
                ) from exc

        if last_exception:

            raise GammaAPIError(
                "Gamma API request failed after retries.\n"
                f"Endpoint: GET {url}\n"
                f"Error: {str(last_exception)}"
            ) from last_exception

        raise GammaAPIError(
            f"Gamma API request failed: GET {url}"
        )

    # ------------------------------------------------------------------
    # Events
    # ------------------------------------------------------------------

    def get_events(
        self,
        *,
        limit: int = 100,
        offset: int = 0,
        **filters,
    ) -> List[Dict[str, Any]]:
        """
        Get a single page of events.

        Example:
            client.get_events(
                limit=100,
                offset=0,
                active=True
            )
        """

        params = {
            "limit": limit,
            "offset": offset,
        }

        # Remove None values.
        params.update(
            {
                key: value
                for key, value in filters.items()
                if value is not None
            }
        )

        response = self.get(
            "/events",
            params=params,
        )

        return self._normalize_list_response(response)

    def get_all_events(
        self,
        *,
        batch_size: int = 100,
        max_pages: Optional[int] = None,
        **filters,
    ) -> List[Dict[str, Any]]:
        """
        Retrieve all events using offset pagination.

        Pagination stops when:
        - API returns an empty page
        - max_pages is reached, if provided
        """

        all_events: List[Dict[str, Any]] = []

        offset = 0
        page = 0

        while True:

            if max_pages is not None and page >= max_pages:
                break

            events = self.get_events(
                limit=batch_size,
                offset=offset,
                **filters,
            )

            if not events:
                break

            all_events.extend(events)

            page += 1
            offset += batch_size

        return all_events

    # ------------------------------------------------------------------
    # Markets
    # ------------------------------------------------------------------

    def get_markets(
        self,
        *,
        limit: int = 100,
        offset: int = 0,
        **filters,
    ) -> List[Dict[str, Any]]:
        """
        Get a single page of markets.
        """

        params = {
            "limit": limit,
            "offset": offset,
        }

        params.update(
            {
                key: value
                for key, value in filters.items()
                if value is not None
            }
        )

        response = self.get(
            "/markets",
            params=params,
        )

        return self._normalize_list_response(response)

    def get_all_markets(
        self,
        *,
        batch_size: int = 100,
        max_pages: Optional[int] = None,
        **filters,
    ) -> List[Dict[str, Any]]:
        """
        Retrieve all markets using offset pagination.

        Pagination stops when:
        - API returns an empty page
        - max_pages is reached, if provided
        """

        all_markets: List[Dict[str, Any]] = []

        offset = 0
        page = 0

        while True:

            if max_pages is not None and page >= max_pages:
                break

            markets = self.get_markets(
                limit=batch_size,
                offset=offset,
                **filters,
            )

            if not markets:
                break

            all_markets.extend(markets)

            page += 1
            offset += batch_size

        return all_markets

    # ------------------------------------------------------------------
    # Individual Events / Markets
    # ------------------------------------------------------------------

    def get_event(
        self,
        event_id: str,
    ) -> Dict[str, Any]:

        response = self.get(
            f"/events/{event_id}"
        )

        if not isinstance(response, dict):

            raise GammaAPIError(
                "Unexpected event response format."
            )

        return response

    def get_event_by_slug(
        self,
        slug: str,
    ) -> Dict[str, Any]:

        response = self.get(
            f"/events/slug/{slug}"
        )

        if not isinstance(response, dict):

            raise GammaAPIError(
                "Unexpected event response format."
            )

        return response

    def get_market(
        self,
        market_id: str,
    ) -> Dict[str, Any]:

        response = self.get(
            f"/markets/{market_id}"
        )

        if not isinstance(response, dict):

            raise GammaAPIError(
                "Unexpected market response format."
            )

        return response

    def get_market_by_slug(
        self,
        slug: str,
    ) -> Dict[str, Any]:

        response = self.get(
            f"/markets/slug/{slug}"
        )

        if not isinstance(response, dict):

            raise GammaAPIError(
                "Unexpected market response format."
            )

        return response

    def get_market_by_token(
        self,
        token_id: str,
    ) -> Dict[str, Any]:

        response = self.get(
            f"/markets/token/{token_id}"
        )

        if not isinstance(response, dict):

            raise GammaAPIError(
                "Unexpected market response format."
            )

        return response

    # ------------------------------------------------------------------
    # Tags
    # ------------------------------------------------------------------

    def get_tags(
        self,
        *,
        limit: int = 100,
        offset: int = 0,
        **filters,
    ) -> List[Dict[str, Any]]:

        params = {
            "limit": limit,
            "offset": offset,
        }

        params.update(
            {
                key: value
                for key, value in filters.items()
                if value is not None
            }
        )

        response = self.get(
            "/tags",
            params=params,
        )

        return self._normalize_list_response(response)

    # ------------------------------------------------------------------
    # Search
    # ------------------------------------------------------------------

    def search(
        self,
        query: str,
    ) -> Any:

        return self.get(
            "/public-search",
            params={
                "q": query,
            },
        )

    # ------------------------------------------------------------------
    # Sports
    # ------------------------------------------------------------------

    def get_sports(self) -> Any:

        return self.get("/sports")

    def get_sports_market_types(self) -> Any:

        return self.get(
            "/sports/market-types"
        )

    def get_teams(self) -> Any:

        return self.get("/teams")
