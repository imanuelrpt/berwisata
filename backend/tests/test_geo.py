"""Unit tests for geo utilities and polyline codec."""
import math

from app.utils.geo import (
    decode_polyline,
    encode_float_list,
    estimate_duration_minutes,
    haversine_km,
)


class TestHaversine:
    def test_same_point_is_zero(self):
        assert haversine_km(0.0, 0.0, 0.0, 0.0) == 0.0

    def test_known_distance(self):
        # Jakarta (-6.2, 106.8) to Bandung (-6.9, 107.6)
        km = haversine_km(-6.2, 106.8, -6.9, 107.6)
        assert 100 <= km <= 130

    def test_round_trip_symmetry(self):
        a = haversine_km(-7.0, 110.0, -8.5, 115.2)
        b = haversine_km(-8.5, 115.2, -7.0, 110.0)
        assert abs(a - b) < 1e-9

    def test_none_coords(self):
        assert haversine_km(None, 1, 2, 3) == 0.0


class TestDuration:
    def test_car(self):
        assert estimate_duration_minutes(55, "driving-car") == pytest_approx(60)

    def test_walk(self):
        assert estimate_duration_minutes(4.8, "foot-walking") == pytest_approx(60)


def pytest_approx(v, places=0):
    return round(v, places)


class TestPolyline:
    def test_round_trip(self):
        coords = [[-6.20000, 106.81667], [-6.50000, 107.00000], [-6.90000, 107.60000]]
        encoded = encode_float_list([v for pair in coords for v in pair])
        decoded = decode_polyline(encoded)
        assert len(decoded) == 3
        for (la, lo), (elat, elon) in zip(coords, decoded):
            assert abs(la - elat) < 0.01
            assert abs(lo - elon) < 0.01

    def test_empty(self):
        assert encode_float_list([]) == ""
        assert decode_polyline("") == []
