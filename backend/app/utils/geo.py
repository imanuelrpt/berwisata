import math
from typing import Optional, Tuple

EARTH_RADIUS_KM = 6371.0088


def haversine_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Great-circle distance in kilometers (fallback when ORS unavailable)."""
    if lat1 is None or lon1 is None or lat2 is None or lon2 is None:
        return 0.0
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lon2 - lon1)
    a = math.sin(dphi / 2) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(dlambda / 2) ** 2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return EARTH_RADIUS_KM * c


def bearing_deg(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dlambda = math.radians(lon2 - lon1)
    y = math.sin(dlambda) * math.cos(phi2)
    x = math.cos(phi1) * math.sin(phi2) - math.sin(phi1) * math.cos(phi2) * math.cos(dlambda)
    return (math.degrees(math.atan2(y, x)) + 360) % 360


# Rough speed assumptions in km/h per transport profile
PROFILE_SPEED_KPH = {
    "driving-car": 55.0,
    "driving-hgv": 45.0,
    "cycling-regular": 16.0,
    "foot-walking": 4.8,
    "car": 55.0,
    "motorcycle": 50.0,
    "walking": 4.8,
    "cycling": 16.0,
}


def estimate_duration_minutes(distance_km: float, profile: str) -> float:
    speed = PROFILE_SPEED_KPH.get(profile, 40.0)
    return round((distance_km / speed) * 60.0, 1)


def destination_distance(
    user_lat: Optional[float],
    user_lon: Optional[float],
    dest_lat: float,
    dest_lon: float,
) -> Optional[float]:
    if user_lat is None or user_lon is None:
        return None
    return round(haversine_km(user_lat, user_lon, dest_lat, dest_lon), 2)


def _encode_delta(delta: int, chunks: list[str]) -> None:
    delta = delta << 1 if delta >= 0 else ~(delta << 1)
    while delta >= 0x20:
        chunks.append(chr((0x20 | (delta & 0x1F)) + 63))
        delta >>= 5
    chunks.append(chr(delta + 63))


def encode_float_list(values: list[float]) -> str:
    """Float polyline encoder compatible with Leaflet Polyline encoded format.

    Input is a flat list ``[lat1, lon1, lat2, lon2, ...]``; deltas are tracked
    per channel (lat-lat, lon-lon) as required by the polyline algorithm.
    """
    if not values:
        return ""
    if len(values) % 2 != 0:
        raise ValueError("encode_float_list requires lat/lon pairs")
    chunks: list[str] = []
    prev_lat = prev_lon = 0
    for i in range(0, len(values), 2):
        lat = round(values[i] * 1e5)
        lon = round(values[i + 1] * 1e5)
        _encode_delta(lat - prev_lat, chunks)
        _encode_delta(lon - prev_lon, chunks)
        prev_lat, prev_lon = lat, lon
    return "".join(chunks)


def decode_polyline(encoded: str) -> list[Tuple[float, float]]:
    points: list[Tuple[float, float]] = []
    index, lat, lon = 0, 0, 0
    while index < len(encoded):
        shift, result, byte = 0, 0, 0
        while True:
            byte = ord(encoded[index]) - 63
            index += 1
            result |= (byte & 0x1F) << shift
            shift += 5
            if byte < 0x20:
                break
        dlat = ~(result >> 1) if result & 1 else result >> 1
        lat += dlat
        shift, result, byte = 0, 0, 0
        while True:
            byte = ord(encoded[index]) - 63
            index += 1
            result |= (byte & 0x1F) << shift
            shift += 5
            if byte < 0x20:
                break
        dlon = ~(result >> 1) if result & 1 else result >> 1
        lon += dlon
        points.append((lat / 1e5, lon / 1e5))
    return points
