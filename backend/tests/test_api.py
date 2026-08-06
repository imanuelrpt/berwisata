"""Integration tests exercising the HTTP API with an in-memory SQLite DB."""
import pytest

DUMMY_WEATHER = {
    "latitude": -6.2,
    "longitude": 106.8,
    "temperature_c": 28.0,
    "feels_like_c": 30.0,
    "condition": "Cerah",
    "weather_code": 0,
    "icon": "☀️",
    "wind_speed_kph": 12.0,
    "wind_direction": 180.0,
    "humidity": 70,
    "precipitation_mm": 0.0,
    "is_day": True,
    "updated_at": "2026-01-01T00:00:00Z",
}


@pytest.fixture(autouse=True)
def _no_external_http(monkeypatch):
    import app.controllers.destination_controller as dc
    import app.controllers.map_controller as mc
    import app.services.weather_service as ws

    monkeypatch.setattr(dc, "get_weather", lambda *a, **k: DUMMY_WEATHER)
    monkeypatch.setattr(mc, "get_weather", lambda *a, **k: DUMMY_WEATHER)
    monkeypatch.setattr(ws, "get_weather", lambda *a, **k: DUMMY_WEATHER)


def _register(client, email="user@berwisata.id"):
    resp = client.post(
        "/api/v1/auth/register",
        json={
            "email": email,
            "username": email.split("@")[0],
            "full_name": "Test User",
            "password": "Strong@123",
        },
    )
    assert resp.status_code == 201, resp.text
    return resp.json()["data"]


class TestAuthFlow:
    def test_register_login_refresh_me(self, client, _no_external_http):
        data = _register(client)
        assert data["tokens"]["access_token"]
        assert data["tokens"]["refresh_token"]

        # login
        login = client.post(
            "/api/v1/auth/login",
            json={"identifier": "user@berwisata.id", "password": "Strong@123"},
        )
        assert login.status_code == 200
        tokens = login.json()["data"]["tokens"]

        # me
        me = client.get(
            "/api/v1/auth/me", headers={"Authorization": f"Bearer {tokens['access_token']}"}
        )
        assert me.status_code == 200
        assert me.json()["data"]["user"]["email"] == "user@berwisata.id"

        # refresh
        ref = client.post(
            "/api/v1/auth/refresh", json={"refresh_token": tokens["refresh_token"]}
        )
        assert ref.status_code == 200
        assert ref.json()["data"]["access_token"]

        # logout
        out = client.post("/api/v1/auth/logout", json={"refresh_token": tokens["refresh_token"]})
        assert out.status_code == 200

    def test_duplicate_email_rejected(self, client, _no_external_http):
        _register(client, email="dup@berwisata.id")
        resp = client.post(
            "/api/v1/auth/register",
            json={
                "email": "dup@berwisata.id",
                "username": "other",
                "full_name": "Other",
                "password": "Strong@123",
            },
        )
        assert resp.status_code == 409

    def test_wrong_password_rejected(self, client, _no_external_http):
        _register(client, email="wrongpw@berwisata.id")
        resp = client.post(
            "/api/v1/auth/login",
            json={"identifier": "wrongpw@berwisata.id", "password": "Wrong@123"},
        )
        assert resp.status_code == 401


class TestDestinations:
    def test_search_returns_seeded(self, client, seed_data, _no_external_http):
        resp = client.post("/api/v1/destinations/search", json={"page": 1, "per_page": 10})
        assert resp.status_code == 200
        body = resp.json()["data"]
        assert body["meta"]["total"] == 1
        assert body["data"][0]["name"] == "Pantai Indah Tersembunyi"

    def test_search_by_province(self, client, seed_data, _no_external_http):
        resp = client.post(
            "/api/v1/destinations/search", json={"province": "Jawa Barat", "per_page": 10}
        )
        assert resp.json()["data"]["meta"]["total"] == 1
        resp = client.post(
            "/api/v1/destinations/search", json={"province": "Papua", "per_page": 10}
        )
        assert resp.json()["data"]["meta"]["total"] == 0

    def test_search_by_tag(self, client, seed_data, _no_external_http):
        resp = client.post("/api/v1/destinations/search", json={"tags": ["pantai"], "per_page": 10})
        assert resp.json()["data"]["meta"]["total"] == 1

    def test_detail(self, client, seed_data, _no_external_http):
        dest_id = seed_data["destination"].id
        resp = client.get(f"/api/v1/destinations/{dest_id}")
        assert resp.status_code == 200
        body = resp.json()["data"]
        assert body["name"] == "Pantai Indah Tersembunyi"
        assert body["weather"] == DUMMY_WEATHER

    def test_detail_not_found(self, client, _no_external_http):
        resp = client.get("/api/v1/destinations/99999")
        assert resp.status_code == 404

    def test_search_sorted_by_hidden_gem(self, client, seed_data, _no_external_http):
        resp = client.post(
            "/api/v1/destinations/search",
            json={"page": 1, "per_page": 10, "sort_by": "hidden_gem", "order": "desc"},
        )
        assert resp.status_code == 200
        scores = [d["hidden_gem_score"] for d in resp.json()["data"]["data"]]
        assert scores == sorted(scores, reverse=True)

    def test_categories(self, client, seed_data, _no_external_http):
        resp = client.get("/api/v1/categories")
        assert resp.status_code == 200
        rows = resp.json()["data"]["data"]
        assert any(c["slug"] == "pantai" for c in rows)


class TestFavorites:
    def test_favorite_requires_auth(self, client, _no_external_http):
        resp = client.get("/api/v1/favorites")
        assert resp.status_code == 401

    def test_favorite_flow(self, client, seed_data, _no_external_http):
        data = _register(client, email="fav@berwisata.id")
        headers = {"Authorization": f"Bearer {data['tokens']['access_token']}"}
        dest_id = seed_data["destination"].id

        add = client.post("/api/v1/favorites", json={"destination_id": dest_id}, headers=headers)
        assert add.status_code == 201

        lst = client.get("/api/v1/favorites", headers=headers)
        assert lst.json()["data"]["data"][0]["id"] == dest_id

        rm = client.delete(f"/api/v1/favorites/{dest_id}", headers=headers)
        assert rm.status_code == 200

        lst2 = client.get("/api/v1/favorites", headers=headers)
        assert lst2.json()["data"]["meta"]["total"] == 0


class TestRatings:
    def test_rating_requires_auth(self, client, seed_data, _no_external_http):
        dest_id = seed_data["destination"].id
        resp = client.post(f"/api/v1/destinations/{dest_id}/ratings", json={"score": 5})
        assert resp.status_code in (401, 403)

    def test_rating_flow(self, client, seed_data, _no_external_http):
        data = _register(client, email="rat@berwisata.id")
        headers = {"Authorization": f"Bearer {data['tokens']['access_token']}"}
        dest_id = seed_data["destination"].id

        add = client.post(
            f"/api/v1/destinations/{dest_id}/ratings",
            json={"score": 4, "comment": "Sangat indah"},
            headers=headers,
        )
        assert add.status_code == 201
        assert add.json()["data"]["rating"]["score"] == 4

        # duplicate submit updates instead of duplicating
        upd = client.post(
            f"/api/v1/destinations/{dest_id}/ratings",
            json={"score": 5},
            headers=headers,
        )
        assert upd.status_code == 201
        assert upd.json()["data"]["updated"] is True
        assert upd.json()["data"]["rating"]["score"] == 5

        lst = client.get(f"/api/v1/destinations/{dest_id}/ratings")
        assert lst.json()["data"]["meta"]["total"] == 1

    def test_rating_invalid_score(self, client, seed_data, _no_external_http):
        data = _register(client, email="ratbad@berwisata.id")
        headers = {"Authorization": f"Bearer {data['tokens']['access_token']}"}
        dest_id = seed_data["destination"].id
        resp = client.post(
            f"/api/v1/destinations/{dest_id}/ratings",
            json={"score": 9},
            headers=headers,
        )
        assert resp.status_code == 400


class TestHealth:
    def test_health(self, client, _no_external_http):
        resp = client.get("/api/v1/health")
        assert resp.status_code == 200
        assert resp.json()["status"] in ("ok", "degraded")
