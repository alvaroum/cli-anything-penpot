"""Configuration persistence for the Penpot CLI."""

from __future__ import annotations

import getpass
import json
import os
import stat
from dataclasses import dataclass
from pathlib import Path
from urllib.parse import urlsplit, urlunsplit


class ConfigError(ValueError):
    """Raised when configuration is missing or invalid."""


@dataclass(frozen=True)
class Config:
    server: str
    token: str

    @property
    def methods_url(self) -> str:
        return f"{self.server}/api/main/methods"


def default_config_path() -> Path:
    override = os.environ.get("PENPOT_CONFIG")
    if override:
        return Path(override).expanduser()
    return Path.home() / ".config" / "penpot-cli" / "config.json"


def normalize_server(value: str) -> str:
    value = value.strip()
    if not value:
        raise ConfigError("Penpot server address cannot be empty")
    if "://" not in value:
        value = f"https://{value}"
    parsed = urlsplit(value)
    if parsed.scheme not in {"http", "https"} or not parsed.netloc:
        raise ConfigError("Penpot server must be an http(s) URL")
    path = parsed.path.rstrip("/")
    suffix = "/api/main/methods"
    if path.endswith(suffix):
        path = path[: -len(suffix)].rstrip("/")
    return urlunsplit((parsed.scheme, parsed.netloc, path, "", "")).rstrip("/")


def load_config(path: Path | None = None) -> Config:
    env_server = os.environ.get("PENPOT_SERVER")
    env_token = os.environ.get("PENPOT_TOKEN")
    if env_server or env_token:
        if not env_server or not env_token:
            raise ConfigError("PENPOT_SERVER and PENPOT_TOKEN must be set together")
        return Config(normalize_server(env_server), env_token)

    path = path or default_config_path()
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise ConfigError(f"No configuration found at {path}") from exc
    except (OSError, json.JSONDecodeError) as exc:
        raise ConfigError(f"Cannot read configuration at {path}: {exc}") from exc
    if not isinstance(data, dict) or not isinstance(data.get("server"), str) or not isinstance(data.get("token"), str):
        raise ConfigError(f"Configuration at {path} must contain string server and token fields")
    if not data["token"]:
        raise ConfigError(f"Configuration at {path} contains an empty token")
    return Config(normalize_server(data["server"]), data["token"])


def save_config(config: Config, path: Path | None = None) -> Path:
    path = path or default_config_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps({"server": config.server, "token": config.token}, indent=2) + "\n", encoding="utf-8")
    path.chmod(stat.S_IRUSR | stat.S_IWUSR)
    return path


def prompt_config(input_fn=input, print_fn=print) -> Config:
    print_fn("Penpot CLI setup")
    server = normalize_server(input_fn("Penpot server address [https://design.penpot.app]: ") or "https://design.penpot.app")
    token_reader = getpass.getpass if input_fn is input else input_fn
    token = token_reader("Penpot auth token: ").strip()
    if not token:
        raise ConfigError("Penpot auth token cannot be empty")
    return Config(server, token)
