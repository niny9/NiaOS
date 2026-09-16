"""Feishu OpenAPI client with token refresh and retries."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta
import json as jsonlib
import logging
import time
from typing import Any, Dict, Optional

import requests

logger = logging.getLogger(__name__)


class FeishuApiError(RuntimeError):
    """Raised when Feishu API returns non-zero business code."""

    def __init__(
        self,
        message: str,
        *,
        code: Optional[int] = None,
        feishu_msg: Optional[str] = None,
        response_body: Optional[Dict[str, Any]] = None,
    ) -> None:
        super().__init__(message)
        self.code = code
        self.feishu_msg = feishu_msg
        self.response_body = response_body


@dataclass
class _TokenCache:
    token: str
    expires_at: datetime


class FeishuClient:
    """Lightweight Feishu client for Bitable APIs."""

    BASE_URL = "https://open.feishu.cn"

    def __init__(
        self,
        app_id: str,
        app_secret: str,
        timeout_seconds: int = 20,
        max_retries: int = 3,
        min_interval_seconds: float = 0.12,
    ) -> None:
        self.app_id = app_id
        self.app_secret = app_secret
        self.timeout_seconds = timeout_seconds
        self.max_retries = max_retries
        self.min_interval_seconds = min_interval_seconds
        self._token_cache: Optional[_TokenCache] = None
        self._last_call_ts = 0.0

    @staticmethod
    def _mask_sensitive(payload: Optional[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
        if payload is None:
            return None
        masked = dict(payload)
        if "app_secret" in masked:
            masked["app_secret"] = "***"
        return masked

    def get_tenant_access_token(self, force_refresh: bool = False) -> str:
        """Get tenant access token with in-memory cache."""
        now = datetime.now()
        if (
            not force_refresh
            and self._token_cache
            and self._token_cache.expires_at > now + timedelta(seconds=60)
        ):
            return self._token_cache.token

        path = "/open-apis/auth/v3/tenant_access_token/internal"
        payload = {"app_id": self.app_id, "app_secret": self.app_secret}
        masked_payload = self._mask_sensitive(payload)
        logger.info("[Feishu] token request url=%s%s", self.BASE_URL, path)
        logger.info("[Feishu] token request payload=%s", masked_payload)

        data = self._request("POST", path, json=payload, with_auth=False, return_full_body=True)
        token = str(data.get("tenant_access_token", "") or "").strip()
        expire = int(data.get("expire", 0) or 0)
        if not token:
            logger.error("[Feishu] Failed to fetch tenant_access_token, response=%s", data)
            raise FeishuApiError("Failed to fetch tenant_access_token")
        self._token_cache = _TokenCache(token=token, expires_at=now + timedelta(seconds=max(expire - 60, 60)))
        return token

    def create_bitable_app(self, name: str, folder_token: str | None = None) -> Dict[str, Any]:
        """Create one Bitable document(app)."""
        payload: Dict[str, Any] = {"name": name}
        if folder_token:
            payload["folder_token"] = folder_token
        return self._request("POST", "/open-apis/bitable/v1/apps", json=payload)

    def create_bitable(self, name: str, folder_token: str | None = None) -> str:
        """Create one Bitable and return app_token."""
        data = self.create_bitable_app(name=name, folder_token=folder_token)
        app_token = ((data.get("app") or {}).get("app_token") or "").strip()
        if not app_token:
            raise FeishuApiError("Failed to create bitable: app_token missing in response")
        return app_token

    def request(
        self,
        method: str,
        path: str,
        *,
        params: Optional[Dict[str, Any]] = None,
        json: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Public API request wrapper."""
        return self._request(method, path, params=params, json=json)

    def _request(
        self,
        method: str,
        path: str,
        *,
        params: Optional[Dict[str, Any]] = None,
        json: Optional[Dict[str, Any]] = None,
        with_auth: bool = True,
        return_full_body: bool = False,
    ) -> Dict[str, Any]:
        url = f"{self.BASE_URL}{path}"
        headers = {"Content-Type": "application/json; charset=utf-8"}
        if with_auth:
            headers["Authorization"] = f"Bearer {self.get_tenant_access_token()}"

        for attempt in range(1, self.max_retries + 1):
            self._respect_rate_limit()
            try:
                resp = requests.request(
                    method=method,
                    url=url,
                    headers=headers,
                    params=params,
                    json=json,
                    timeout=max(self.timeout_seconds, 10),
                )
                logger.info("[Feishu] response status=%s path=%s", resp.status_code, path)
                logger.info("[Feishu] response body=%s", resp.text)
                if resp.status_code == 401 and with_auth:
                    headers["Authorization"] = f"Bearer {self.get_tenant_access_token(force_refresh=True)}"
                    continue
                # Check business error code first before raising HTTP errors
                body = resp.json()
                if int(body.get("code", -1)) != 0:
                    code = int(body.get("code", -1))
                    msg = str(body.get("msg", "") or "")
                    logger.error("[Feishu] business error path=%s body=%s", path, body)
                    raise FeishuApiError(
                        f"Feishu business error code={code} msg={msg}",
                        code=code,
                        feishu_msg=msg,
                        response_body=body,
                    )
                # Only raise HTTP errors if business code is 0
                resp.raise_for_status()
                if return_full_body:
                    return body
                return body.get("data", {})
            except FeishuApiError as e:
                # Business errors (code != 0) should not be retried
                logger.exception(
                    "[Feishu] request failed attempt=%s/%s method=%s path=%s params=%s body=%s",
                    attempt,
                    self.max_retries,
                    method,
                    path,
                    params,
                    jsonlib.dumps(self._mask_sensitive(json), ensure_ascii=False) if json is not None else None,
                )
                raise  # Don't retry business errors
            except (requests.RequestException, ValueError):
                logger.exception(
                    "[Feishu] request failed attempt=%s/%s method=%s path=%s params=%s body=%s",
                    attempt,
                    self.max_retries,
                    method,
                    path,
                    params,
                    jsonlib.dumps(self._mask_sensitive(json), ensure_ascii=False) if json is not None else None,
                )
                if attempt >= self.max_retries:
                    raise
                time.sleep(min(2.0, 0.5 * attempt))

        raise FeishuApiError("Unknown request failure")

    def _respect_rate_limit(self) -> None:
        now = time.time()
        wait = self.min_interval_seconds - (now - self._last_call_ts)
        if wait > 0:
            time.sleep(wait)
        self._last_call_ts = time.time()
