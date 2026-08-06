"""Weather service backed by Open-Meteo (free, no API key). Cached in-process."""
import logging
import threading
import time
from datetime import datetime, timezone
from typing import Any, Optional

import httpx

from app.core.config import settings

logger = logging.getLogger("app.weather")

WMO_CODES = {
    0: ("Cerah", "☀️"),
    1: ("Cerah Berawan", "🌤️"),
    2: ("Berawan", "⛅"),
    3: ("Mendung", "☁️"),
    45: ("Kabut", "🌫️"),
    48: ("Kabut Membeku", "🌫️"),
    51: ("Gerimis Ringan", "🌦️"),
    53: ("Gerimis", "🌦️"),
    55: ("Gerimis Lebat", "🌧️"),
    61: ("Hujan Ringan", "🌧️"),
    63: ("Hujan", "🌧️"),
    65: ("Hujan Lebat", "⛈️"),
    71: ("Salju Ringan", "🌨️"),
    73: ("Salju", "🌨️"),
    75: ("Salju Lebat", "❄️"),
    80: ("Hujan Lokal", "🌦️"),
    81: ("Hujan Lokal Lebat", "🌧️"),
    82: ("Hujan Badai", "⛈️"),
    95: ("Badai Petir", "⛈️"),
    96: ("Badai Petir + Hujan Es", "⛈️"),
    99: ("Badai Petir Lebat + Hujan Es", "⛈️"),
}

_cache: dict[str, tuple[float, dict]] = {}
_lock = threading.Lock()


def _condition(code: int) -> str:
    return WMO_CODES.get(int(code), ("Tidak Diketahui", "🌤️"))[0]


def _icon(code: int) -> str:
    return WMO_CODES.get(int(code), ("Tidak Diketahui", "🌤️"))[1]


def get_weather(
    latitude: float,
    longitude: float,
    force_refresh: bool = False,
    timeout: float = 8.0,
) -> dict[str, Any]:
    """Return current weather for coordinates. Uses cache to limit external calls."""
    key = f"{latitude:.4f},{longitude:.4f}"
    now = time.time()

    with _lock:
        cached = _cache.get(key)
        if cached and not force_refresh and now - cached[0] < settings.WEATHER_CACHE_TTL_SECONDS:
            return cached[1]

    params = {
        "latitude": latitude,
        "longitude": longitude,
        "current": "temperature_2m,relative_humidity_2m,apparent_temperature,weather_code,wind_speed_10m,wind_direction_10m,precipitation,is_day",
        "timezone": "auto",
        "wind_speed_unit": "kmh",
    }

    try:
        with httpx.Client(timeout=timeout) as client:
            resp = client.get(f"{settings.WEATHER_BASE_URL}/forecast", params=params)
            resp.raise_for_status()
            data = resp.json()
        current = data.get("current", {})
        result = {
            "latitude": round(float(current.get("latitude", latitude)), 6),
            "longitude": round(float(current.get("longitude", longitude)), 6),
            "temperature_c": round(float(current.get("temperature_2m", 0)), 1),
            "feels_like_c": round(float(current.get("apparent_temperature", 0)), 1),
            "condition": _condition(current.get("weather_code", 0)),
            "weather_code": int(current.get("weather_code", 0)),
            "icon": _icon(current.get("weather_code", 0)),
            "wind_speed_kph": round(float(current.get("wind_speed_10m", 0)), 1),
            "wind_direction": round(float(current.get("wind_direction_10m", 0)), 1),
            "humidity": int(current.get("relative_humidity_2m", 0)),
            "precipitation_mm": round(float(current.get("precipitation", 0)), 2),
            "is_day": bool(current.get("is_day", 1)),
            "updated_at": datetime.now(timezone.utc).isoformat(),
        }
    except Exception as exc:  # pragma: no cover - external service
        logger.warning("Weather fetch failed (%s): %s", key, exc)
        result = {
            "latitude": round(float(latitude), 6),
            "longitude": round(float(longitude), 6),
            "temperature_c": 0.0,
            "feels_like_c": 0.0,
            "condition": "Tidak tersedia",
            "weather_code": -1,
            "icon": "🌤️",
            "wind_speed_kph": 0.0,
            "wind_direction": 0.0,
            "humidity": 0,
            "precipitation_mm": 0.0,
            "is_day": True,
            "updated_at": datetime.now(timezone.utc).isoformat(),
        }

    with _lock:
        _cache[key] = (now, result)
    return result


def attach_weather(destinations: list[dict], lat_attr: str = "latitude", lon_attr: str = "longitude") -> list[dict]:
    """Attach weather to each destination dict."""
    for d in destinations:
        if d.get(lat_attr) is not None and d.get(lon_attr) is not None:
            d["weather"] = get_weather(float(d[lat_attr]), float(d[lon_attr]))
    return destinations
