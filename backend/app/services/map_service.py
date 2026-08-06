"""Map & routing service.

Primary: OpenRouteService API for real road/off-road routes.
Fallback: Haversine straight-line distance with profile speed estimate.
"""
import logging
from typing import Any, Optional

import httpx

from app.core.config import settings
from app.utils.geo import decode_polyline, estimate_duration_minutes, haversine_km

logger = logging.getLogger("app.map")

PROFILE_MAP = {
    "car": "driving-car",
    "motorcycle": "driving-car",
    "walking": "foot-walking",
    "cycling": "cycling-regular",
}

ROUTE_WARNINGS = {
    "No path could be found for given query": "Rute tidak ditemukan, menggunakan jarak garis lurus",
}


def _ors_enabled() -> bool:
    return bool(settings.ORS_API_KEY)


def get_route(
    origin_lat: float,
    origin_lon: float,
    dest_lat: float,
    dest_lon: float,
    transport: str = "car",
    timeout: float = 10.0,
) -> dict[str, Any]:
    """Return route with distance, duration, geometry (polyline + coords)."""
    warnings: list[str] = []
    profile = PROFILE_MAP.get(transport, "driving-car")

    if _ors_enabled():
        try:
            result = _call_ors(origin_lat, origin_lon, dest_lat, dest_lon, profile, timeout)
            if result["success"]:
                return result["data"]
            warnings.append(result["message"])
        except Exception as exc:  # pragma: no cover
            logger.warning("ORS routing failed (%s): %s", transport, exc)
            warnings.append("Layanan rute tidak tersedia, menggunakan jarak garis lurus")
    else:
        warnings.append("ORS_API_KEY belum dikonfigurasi, menggunakan jarak garis lurus")

    # Haversine fallback
    distance_km = haversine_km(origin_lat, origin_lon, dest_lat, dest_lon)
    duration = estimate_duration_minutes(distance_km, profile)
    return {
        "distance_km": round(distance_km, 2),
        "duration_minutes": round(duration, 1),
        "polyline": "",
        "geometry": [[origin_lat, origin_lon], [dest_lat, dest_lon]],
        "profile": profile,
        "source": "haversine",
        "warnings": warnings,
    }


def _call_ors(lat1: float, lon1: float, lat2: float, lon2: float, profile: str, timeout: float) -> dict:
    url = f"{settings.ORS_BASE_URL}/directions/{profile}"
    headers = {"Authorization": settings.ORS_API_KEY, "Accept": "application/json, application/geo+json"}
    body = {
        "coordinates": [[lon1, lat1], [lon2, lat2]],
        "units": "km",
        "geometry": True,
        "instructions": False,
        "elevation": False,
    }
    with httpx.Client(timeout=timeout) as client:
        resp = client.post(url, json=body, headers=headers)
        resp.raise_for_status()
        payload = resp.json()

    if payload.get("routes"):
        route = payload["routes"][0]
        geometry = route.get("geometry")
        if isinstance(geometry, dict):
            coords = geometry.get("coordinates", [])
            polyline = ""
        elif isinstance(geometry, str):
            coords = decode_polyline(geometry)
            polyline = geometry
        else:
            coords = [[lon1, lat1], [lon2, lat2]]
            polyline = ""
        distance_km = float(route.get("summary", {}).get("distance", 0))
        duration_s = float(route.get("summary", {}).get("duration", 0))
        return {
            "success": True,
            "data": {
                "distance_km": round(distance_km, 2),
                "duration_minutes": round(duration_s / 60.0, 1),
                "polyline": polyline,
                "geometry": [[float(c[1]), float(c[0])] for c in coords],
                "profile": profile,
                "source": "ors",
                "warnings": [],
            },
        }
    msg = payload.get("error", {}).get("message", "ORS returned no route")
    return {"success": False, "message": ROUTE_WARNINGS.get(msg, msg)}


def distance_matrix(user_lat: float, user_lon: float, destinations: list[dict]) -> list[dict]:
    """Attach distance + ETA to destination dicts. Uses ORS per destination, haversine fallback."""
    for d in destinations:
        try:
            route = get_route(
                user_lat, user_lon, float(d["latitude"]), float(d["longitude"]), transport="car"
            )
            d["distance_km"] = route["distance_km"]
            d["duration_minutes"] = route["duration_minutes"]
            d["route_source"] = route["source"]
        except Exception:  # pragma: no cover
            km = haversine_km(user_lat, user_lon, float(d["latitude"]), float(d["longitude"]))
            d["distance_km"] = round(km, 2)
            d["duration_minutes"] = estimate_duration_minutes(km, "driving-car")
            d["route_source"] = "haversine"
    return destinations
