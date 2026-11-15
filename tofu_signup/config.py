"""Settings loaded from .streamlit/secrets.toml, environment variables, or a git-ignored .env file.

secrets.toml wins over the environment when a key is set in both.
"""

import os
from dataclasses import dataclass

import streamlit as st
from dotenv import load_dotenv


@dataclass(frozen=True)
class Config:
    invite_code: str
    soap_url: str
    soap_user: str
    soap_pass: str
    invite_max_fails: int
    creates_per_hour: int
    debug: bool


def _get(key: str, default: str | None = None) -> str | None:
    try:
        if key in st.secrets:
            return str(st.secrets[key])
    except Exception:  # no secrets.toml present
        pass
    return os.environ.get(key, default)


def load_config() -> Config:
    load_dotenv()
    missing = [k for k in ("TOFU_INVITE_CODE", "TOFU_SOAP_USER", "TOFU_SOAP_PASS") if not _get(k)]
    if missing:
        raise RuntimeError(f"Missing required settings: {', '.join(missing)}")
    return Config(
        invite_code=_get("TOFU_INVITE_CODE"),
        soap_url=_get("TOFU_SOAP_URL", "http://127.0.0.1:7878/"),
        soap_user=_get("TOFU_SOAP_USER"),
        soap_pass=_get("TOFU_SOAP_PASS"),
        invite_max_fails=int(_get("TOFU_INVITE_MAX_FAILS", "5")),
        creates_per_hour=int(_get("TOFU_CREATES_PER_HOUR", "10")),
        debug=_get("TOFU_DEBUG", "0") == "1",
    )
