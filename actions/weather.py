"""
Basit hava durumu ozeti — uzaktaki bir servis uzerinden calisir.
LEO — Proprietary. All rights reserved.

Varsayilan konum:
- LEO_WEATHER_LOCATION veya config location
- yoksa Lezhë, Albania
"""

from __future__ import annotations

import os

import requests

from app_config import get_default_location


def get_weather_summary(location: str | None = None) -> str:
    target = (
        location
        or os.environ.get("LEO_WEATHER_LOCATION")
        or os.environ.get("JARVIS_WEATHER_LOCATION")
        or get_default_location()
    ).strip()
    try:
        response = requests.get(
            f"https://wttr.in/{target}",
            params={"format": "j1"},
            timeout=10,
            headers={"User-Agent": "LEO"},
        )
        response.raise_for_status()
        payload = response.json()
        current = (payload.get("current_condition") or [{}])[0]
        temp_c = current.get("temp_C")
        feels_like = current.get("FeelsLikeC")
        weather_desc = ((current.get("weatherDesc") or [{}])[0]).get("value", "")
        humidity = current.get("humidity")

        parts = []
        if temp_c:
            parts.append(f"{temp_c} derece")
        if weather_desc:
            parts.append(weather_desc.lower())
        if feels_like and feels_like != temp_c:
            parts.append(f"hissedilen {feels_like} derece")
        if humidity:
            parts.append(f"nem yüzde {humidity}")

        if not parts:
            return "Hava durumu bilgisi şu anda alınamadı."

        return f"{target} için hava durumu: " + ", ".join(parts) + "."
    except Exception:
        return "Hava durumu bilgisi şu anda alınamadı."
