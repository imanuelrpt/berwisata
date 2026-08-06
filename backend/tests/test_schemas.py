"""Pydantic schema validation tests."""
import pytest
from pydantic import ValidationError

from app.schemas.auth import LoginRequest, RegisterRequest
from app.schemas.destination import DestinationCreate
from app.schemas.search import SearchRequest


class TestRegisterRequest:
    def test_valid(self):
        data = RegisterRequest(
            email="user@test.id",
            username="traveler_1",
            full_name="Budi Santoso",
            password="Strong@123",
        )
        assert data.email == "user@test.id"

    def test_weak_password_rejected(self):
        with pytest.raises(ValidationError):
            RegisterRequest(
                email="user@test.id", username="traveler", full_name="Budi", password="weakpass"
            )

    def test_invalid_username_rejected(self):
        with pytest.raises(ValidationError):
            RegisterRequest(
                email="user@test.id", username="bad username!", full_name="Budi", password="Strong@123"
            )


class TestLoginRequest:
    def test_identifier_and_password(self):
        data = LoginRequest(identifier="user@test.id", password="Strong@123")
        assert data.identifier == "user@test.id"


class TestDestinationCreate:
    def test_valid_coordinates(self):
        d = DestinationCreate(
            name="Pantai Test", category_id=1, address="Jl Test No 1",
            province="Bali", regency="Badung", latitude=-8.5, longitude=115.1,
        )
        assert d.latitude == -8.5

    def test_invalid_latitude_rejected(self):
        with pytest.raises(ValidationError):
            DestinationCreate(
                name="Pantai Test", category_id=1, address="Jl Test No 1",
                province="Bali", regency="Badung", latitude=95.0, longitude=115.1,
            )

    def test_invalid_time_rejected(self):
        with pytest.raises(ValidationError):
            DestinationCreate(
                name="Pantai Test", category_id=1, address="Jl Test No 1",
                province="Bali", regency="Badung", latitude=-8.5, longitude=115.1,
                opening_time="25:99",
            )


class TestSearchRequest:
    def test_defaults(self):
        s = SearchRequest()
        assert s.page == 1
        assert s.per_page == 12

    def test_valid_sort(self):
        s = SearchRequest(sort_by="hidden_gem")
        assert s.sort_by == "hidden_gem"

    def test_invalid_sort_rejected(self):
        with pytest.raises(ValidationError):
            SearchRequest(sort_by="nonsense")
