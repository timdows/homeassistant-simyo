"""Async client for the Simyo (mijn.simyo.nl) app API.

The app talks to ``https://appapi.simyo.nl/simyoapi/api/v1``. Login takes a
phone number and password and returns a session token, which is then sent on
subsequent calls in the ``X-Session-Token`` header.

Verified endpoints: ``sessions``, ``balance``, ``usage``. Other endpoints
(``settings``, ``address``, ``esim/get-by-customer``) are reachable but not
used here.
"""

from __future__ import annotations

from typing import Any

import aiohttp

from .const import API_BASE, CLIENT_PLATFORM, CLIENT_VERSION, USER_AGENT


class SimyoAuthError(Exception):
    """Raised when the credentials are rejected."""


class SimyoApiError(Exception):
    """Raised on any other API failure."""


class SimyoClient:
    """Minimal Simyo app-API client."""

    def __init__(
        self,
        session: aiohttp.ClientSession,
        phone_number: str,
        password: str,
    ) -> None:
        self._session = session
        self._phone_number = phone_number
        self._password = password
        self._session_token: str | None = None

    @property
    def phone_number(self) -> str:
        return self._phone_number

    def _headers(self, *, with_session: bool = True) -> dict[str, str]:
        headers = {
            "Content-Type": "application/json",
            "Accept": "application/json",
            "User-Agent": USER_AGENT,
            "X-Client-Platform": CLIENT_PLATFORM,
            "X-Client-Version": CLIENT_VERSION,
        }
        if with_session and self._session_token:
            headers["X-Session-Token"] = self._session_token
        return headers

    async def login(self) -> None:
        """Authenticate and store the session token."""
        url = f"{API_BASE}/sessions"
        payload = {"phoneNumber": self._phone_number, "password": self._password}
        try:
            async with self._session.post(
                url, json=payload, headers=self._headers(with_session=False)
            ) as resp:
                data = await resp.json(content_type=None)
                if resp.status == 401 or resp.status == 403:
                    raise SimyoAuthError(
                        data.get("message", "Authentication failed")
                    )
                if resp.status >= 400:
                    raise SimyoApiError(
                        f"Login failed ({resp.status}): {data}"
                    )
        except aiohttp.ClientError as err:
            raise SimyoApiError(f"Login transport error: {err}") from err

        token = self._extract_session_token(data)
        if not token:
            raise SimyoApiError(f"Login response missing session token: {data}")
        self._session_token = token

    @staticmethod
    def _extract_session_token(data: Any) -> str | None:
        if not isinstance(data, dict):
            return None
        for key in ("sessionToken", "session_token", "token"):
            if key in data and isinstance(data[key], str):
                return data[key]
        result = data.get("result")
        if isinstance(result, dict):
            for key in ("sessionToken", "session_token", "token"):
                if key in result and isinstance(result[key], str):
                    return result[key]
        return None

    async def _get(self, path: str) -> Any:
        if not self._session_token:
            await self.login()
        url = f"{API_BASE}/{path}"
        try:
            async with self._session.get(url, headers=self._headers()) as resp:
                data = await resp.json(content_type=None)
                if resp.status == 401:
                    self._session_token = None
                    await self.login()
                    async with self._session.get(
                        url, headers=self._headers()
                    ) as retry:
                        data = await retry.json(content_type=None)
                        if retry.status >= 400:
                            raise SimyoApiError(
                                f"GET {path} failed ({retry.status}): {data}"
                            )
                        return data
                if resp.status >= 400:
                    raise SimyoApiError(f"GET {path} failed ({resp.status}): {data}")
                return data
        except aiohttp.ClientError as err:
            raise SimyoApiError(f"GET {path} transport error: {err}") from err

    async def get_balance(self) -> Any:
        """Return the raw response from the balance endpoint."""
        return await self._get("balance")

    async def get_usage(self) -> Any:
        """Return the raw response from the usage endpoint."""
        return await self._get("usage")

    async def fetch_all(self) -> dict[str, Any]:
        """Fetch every supported endpoint and return them by name."""
        return {
            "balance": await self.get_balance(),
            "usage": await self.get_usage(),
        }
