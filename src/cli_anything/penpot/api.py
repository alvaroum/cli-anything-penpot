"""Small stdlib-only client for Penpot's JSON RPC API."""

from __future__ import annotations

import json
import urllib.error
import urllib.request
from dataclasses import dataclass
from typing import Any

from .config import Config


class ApiError(RuntimeError):
    """An HTTP, transport, or Penpot API error."""

    def __init__(self, message: str, *, status: int | None = None, body: Any = None):
        super().__init__(message)
        self.status = status
        self.body = body


@dataclass
class PenpotApi:
    config: Config
    timeout: float = 30.0

    def post(self, method: str, payload: dict[str, Any] | None = None, *, auth: bool = True) -> Any:
        url = f"{self.config.methods_url}/{method}"
        headers = {"Accept": "application/json", "Content-Type": "application/json"}
        if auth:
            headers["Authorization"] = f"Token {self.config.token}"
        request = urllib.request.Request(
            url,
            data=json.dumps(payload or {}).encode("utf-8"),
            headers=headers,
            method="POST",
        )
        try:
            with urllib.request.urlopen(request, timeout=self.timeout) as response:
                raw = response.read()
                status = response.status
        except urllib.error.HTTPError as exc:
            raw = exc.read()
            body = _decode(raw)
            detail = _error_detail(body) or exc.reason
            raise ApiError(f"Penpot returned HTTP {exc.code}: {detail}", status=exc.code, body=body) from exc
        except (urllib.error.URLError, TimeoutError) as exc:
            raise ApiError(f"Cannot reach Penpot at {self.config.server}: {exc}") from exc

        body = _decode(raw)
        if status < 200 or status >= 300:
            raise ApiError(f"Penpot returned HTTP {status}: {_error_detail(body) or 'request failed'}", status=status, body=body)
        return body

    def verify_token(self) -> Any:
        return self.post("verify-token", {"token": self.config.token}, auth=False)

    def profile(self) -> Any:
        return self.post("get-profile")

    def teams(self) -> Any:
        return self.post("get-owned-teams")

    def projects(self, team_id: str) -> Any:
        return self.post("get-projects", {"teamId": team_id})

    def files(self, project_id: str) -> Any:
        return self.post("get-project-files", {"projectId": project_id})

    def page(self, file_id: str, page_id: str | None = None, object_id: str | None = None) -> Any:
        payload: dict[str, Any] = {"fileId": file_id}
        if page_id:
            payload["pageId"] = page_id
        if object_id:
            payload["objectId"] = object_id
        return self.post("get-page", payload)


def _decode(raw: bytes) -> Any:
    if not raw:
        return None
    try:
        return json.loads(raw.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError):
        return raw.decode("utf-8", errors="replace")


def _error_detail(body: Any) -> str | None:
    if isinstance(body, dict):
        for key in ("message", "error", "type"):
            if body.get(key):
                return str(body[key])
    if isinstance(body, str) and body.strip():
        return body.strip()[:300]
    return None
