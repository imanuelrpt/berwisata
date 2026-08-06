"""Unit tests for security helpers (hashing + JWT)."""
import pytest

from app.core.security import (
    create_access_token,
    create_refresh_token,
    decode_token,
    hash_password,
    verify_password,
)


class TestPasswordHashing:
    def test_hash_and_verify(self):
        hashed = hash_password("Secret@123")
        assert hashed != "Secret@123"
        assert verify_password("Secret@123", hashed)
        assert not verify_password("Wrong@123", hashed)

    def test_unique_salts(self):
        assert hash_password("Secret@123") != hash_password("Secret@123")

    def test_invalid_hash(self):
        assert not verify_password("x", "not-a-hash")


class TestJWT:
    def test_access_token_roundtrip(self):
        token = create_access_token("user@test.id", "admin", 1)
        payload = decode_token(token, expected_type="access")
        assert payload["sub"] == "user@test.id"
        assert payload["role"] == "admin"
        assert payload["uid"] == 1

    def test_refresh_token_type(self):
        token = create_refresh_token("user@test.id", 2)
        payload = decode_token(token, expected_type="refresh")
        assert payload["uid"] == 2

    def test_wrong_type_rejected(self):
        token = create_access_token("a@b.c", "user", 3)
        with pytest.raises(ValueError):
            decode_token(token, expected_type="refresh")

    def test_invalid_token(self):
        with pytest.raises(ValueError):
            decode_token("garbage.token.here", expected_type="access")
