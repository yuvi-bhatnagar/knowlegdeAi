import pytest
from app.core.security import get_password_hash, verify_password, create_access_token, decode_access_token
from app.core.exceptions import AuthenticationException


def test_argon2_password_hashing_and_verification():
    raw_password = "SuperSecretPassword123!"
    hashed = get_password_hash(raw_password)

    # Hash should be non-empty and start with argon2 prefix
    assert hashed.startswith("$argon2")
    assert hashed != raw_password

    # Correct password verifies
    assert verify_password(raw_password, hashed) is True

    # Incorrect password fails
    assert verify_password("WrongPassword!", hashed) is False

    # Empty or malformed hash fails safely
    assert verify_password(raw_password, "not_a_real_hash") is False


def test_jwt_access_token_creation_and_decoding():
    subject_id = "123e4567-e89b-12d3-a456-426614174000"
    token = create_access_token(subject=subject_id)

    assert isinstance(token, str)
    assert len(token) > 20

    payload = decode_access_token(token)
    assert payload["sub"] == subject_id
    assert payload["type"] == "access"
    assert "exp" in payload
    assert "iat" in payload


def test_jwt_invalid_token_handling():
    with pytest.raises(AuthenticationException):
        decode_access_token("invalid.jwt.token")
