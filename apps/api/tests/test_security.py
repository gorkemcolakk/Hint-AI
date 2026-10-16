import jwt
import pytest

from app.core import security


def test_hash_and_verify_password() -> None:
    hashed = security.hash_password("gizli-parola-123")
    assert hashed != "gizli-parola-123"
    assert security.verify_password("gizli-parola-123", hashed)
    assert not security.verify_password("yanlis-parola", hashed)


def test_refresh_token_hash() -> None:
    token = security.new_refresh_token()
    hashed = security.hash_refresh_token(token)
    assert token != hashed
    assert security.hash_refresh_token(token) == hashed


def test_pairing_code_format() -> None:
    code = security.new_pairing_code()
    assert len(code) == 6
    assert code.isdigit()
    assert security.hash_pairing_code(code) == security.hash_pairing_code(code)


def test_access_token_roundtrip() -> None:
    token = security.create_access_token("child-123", "child", 5)
    payload = security.decode_token(token)
    assert payload["sub"] == "child-123"
    assert payload["role"] == "child"
    assert payload["type"] == "access"


def test_decode_tampered_token_fails() -> None:
    token = security.create_access_token("x", "guardian", 5)
    with pytest.raises(jwt.exceptions.InvalidTokenError):
        security.decode_token(token + "bozuk")
