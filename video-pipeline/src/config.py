"""Configuration loading: secrets from the environment, behaviour from JSON.

Secrets (API keys) live in environment variables / .env so they never touch
source control. Everything else (which platforms, caption shapes, per-platform
options) lives in config.json so it's easy to tweak without editing code.
"""
from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any

_DEFAULTS: dict[str, Any] = {
    "platforms": ["linkedin", "youtube", "tiktok", "instagram"],
    "captions": {},
    "platform_options": {},
}


def _load_dotenv(path: Path) -> None:
    """Minimal .env loader so there's no hard dependency on python-dotenv."""
    if not path.exists():
        return
    for line in path.read_text().splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, value = line.partition("=")
        # Don't clobber values already exported in the real environment.
        os.environ.setdefault(key.strip(), value.strip())


def load_config(config_path: str | None = None, env_path: str | None = None) -> dict[str, Any]:
    """Load secrets into os.environ and return the behaviour config dict."""
    root = Path(__file__).resolve().parent.parent
    _load_dotenv(Path(env_path) if env_path else root / ".env")

    path = Path(config_path) if config_path else root / "config.json"
    cfg = dict(_DEFAULTS)
    if path.exists():
        cfg.update(json.loads(path.read_text()))
    return cfg


def require_env(name: str) -> str:
    value = os.environ.get(name)
    if not value:
        raise RuntimeError(
            f"Missing required environment variable {name!r}. "
            f"Copy .env.example to .env and fill it in."
        )
    return value
