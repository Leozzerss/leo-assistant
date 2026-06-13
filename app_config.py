# LEO — Proprietary. All rights reserved.
from __future__ import annotations

import json
import os
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent
CONFIG_DIR = BASE_DIR / "config"
CONFIG_PATH = CONFIG_DIR / "api_keys.json"

# Varsayılan konum: Arnavutluk
DEFAULT_LOCATION = "Lezhë"
DEFAULT_COUNTRY = "Albania"
DEFAULT_TIMEZONE = "Europe/Tirane"

DEFAULT_CONFIG = {
    "gemini_api_key": "",
    "voice": "Charon",
    "youtube_api_key": "",
    "youtube_channel_handle": "",
    "location": DEFAULT_LOCATION,
    "country": DEFAULT_COUNTRY,
    "timezone": DEFAULT_TIMEZONE,
}


def load_app_config() -> dict:
    config = dict(DEFAULT_CONFIG)
    try:
        raw = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
        if isinstance(raw, dict):
            config.update(raw)
    except Exception:
        pass
    return config


def save_app_config(updates: dict) -> dict:
    config = load_app_config()
    for key, value in (updates or {}).items():
        if value is None:
            continue
        config[key] = value
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    CONFIG_PATH.write_text(
        json.dumps(config, indent=4, ensure_ascii=False),
        encoding="utf-8",
    )
    return config


def get_app_config_value(key: str, default=None):
    return load_app_config().get(key, default)


def has_gemini_api_key() -> bool:
    value = str(get_app_config_value("gemini_api_key", "") or "").strip()
    if value:
        return True
    return bool(str(os.environ.get("GEMINI_API_KEY", "") or "").strip())


def get_default_location() -> str:
    cfg = load_app_config()
    location = str(cfg.get("location", DEFAULT_LOCATION) or DEFAULT_LOCATION).strip()
    country = str(cfg.get("country", DEFAULT_COUNTRY) or DEFAULT_COUNTRY).strip()
    if country and country.lower() not in location.lower():
        return f"{location}, {country}"
    return location
