"""Async WooCommerce REST API v3 client."""

from typing import Any

import httpx


class WooCommerceError(Exception):
    """WooCommerce API error with status code and details."""

    def __init__(self, code: str, message: str, status: int):
        self.code = code
        self.message = message
        self.status = status
        super().__init__(f"{status} {code}: {message}")


class WooCommerceClient:
    """Lightweight async client for the WooCommerce REST API v3.

    Auth: HTTP Basic with consumer_key:consumer_secret over HTTPS.
    """

    def __init__(self, store_url: str, consumer_key: str, consumer_secret: str):
        # Normalize: strip trailing slash, ensure /wp-json/wc/v3
        base = store_url.rstrip("/")
        if not base.startswith(("https://", "http://")):
            base = f"https://{base}"
        if not base.endswith("/wp-json/wc/v3"):
            base = f"{base}/wp-json/wc/v3"
        self.base_url = base
        self.store_url = store_url.rstrip("/")
        self._client = httpx.AsyncClient(
            base_url=self.base_url,
            auth=(consumer_key, consumer_secret),
            headers={"Accept": "application/json"},
            timeout=30.0,
            follow_redirects=True,
        )

    async def _request(self, method: str, path: str, **kwargs: Any) -> Any:
        resp = await self._client.request(method, path, **kwargs)
        if resp.status_code == 204:
            return {"success": True}
        try:
            data = resp.json()
        except Exception:
            data = {"code": "parse_error", "message": resp.text}
        if resp.status_code >= 400:
            if isinstance(data, dict):
                raise WooCommerceError(
                    data.get("code", "unknown_error"),
                    data.get("message", "No details provided"),
                    resp.status_code,
                )
            raise WooCommerceError("unknown_error", str(data), resp.status_code)
        return data

    async def get(self, path: str, params: dict[str, Any] | None = None) -> Any:
        return await self._request("GET", path, params=params)

    async def post(self, path: str, json: dict[str, Any] | None = None) -> Any:
        return await self._request("POST", path, json=json or {})

    async def put(self, path: str, json: dict[str, Any]) -> Any:
        return await self._request("PUT", path, json=json)

    async def delete(self, path: str, params: dict[str, Any] | None = None) -> Any:
        return await self._request("DELETE", path, params=params)

    async def close(self) -> None:
        await self._client.aclose()
