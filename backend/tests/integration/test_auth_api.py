import pytest
from httpx import AsyncClient
from app.models.user import User


@pytest.mark.asyncio
async def test_register_success(client: AsyncClient):
    response = await client.post(
        "/api/v1/auth/register",
        json={"email": "newuser@example.com", "password": "StrongPassword123!"},
    )
    assert response.status_code == 201
    data = response.json()
    assert data["email"] == "newuser@example.com"
    assert "id" in data
    assert data["is_active"] is True


@pytest.mark.asyncio
async def test_register_duplicate_email_fails(client: AsyncClient, test_user: User):
    response = await client.post(
        "/api/v1/auth/register",
        json={"email": test_user.email, "password": "AnotherPassword123!"},
    )
    assert response.status_code == 409
    data = response.json()
    assert data["error"]["code"] == "ALREADY_EXISTS"


@pytest.mark.asyncio
async def test_login_success(client: AsyncClient, test_user: User):
    response = await client.post(
        "/api/v1/auth/login",
        json={"email": test_user.email, "password": "ValidPass123!"},
    )
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"
    assert data["expires_in_seconds"] > 0


@pytest.mark.asyncio
async def test_login_invalid_credentials(client: AsyncClient, test_user: User):
    response = await client.post(
        "/api/v1/auth/login",
        json={"email": test_user.email, "password": "WrongPassword!"},
    )
    assert response.status_code == 401
    data = response.json()
    assert data["error"]["code"] == "UNAUTHORIZED"


@pytest.mark.asyncio
async def test_get_me_authenticated(client: AsyncClient, test_user: User, auth_headers: dict[str, str]):
    response = await client.get("/api/v1/auth/me", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == str(test_user.id)
    assert data["email"] == test_user.email


@pytest.mark.asyncio
async def test_get_me_unauthorized(client: AsyncClient):
    response = await client.get("/api/v1/auth/me")
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_email_only_signup_and_set_password_flow(client: AsyncClient):
    from unittest.mock import patch
    from app.services.email_service import EmailService

    email = "mailinator_test@mailinator.com"
    captured_tokens = []
    original_send = EmailService.send_set_password_email

    def intercept_send(recipient_email: str, token: str):
        captured_tokens.append(token)
        return original_send(recipient_email, token)

    # Step 1: User requests signup with email only
    with patch.object(EmailService, "send_set_password_email", side_effect=intercept_send):
        signup_res = await client.post("/api/v1/auth/signup", json={"email": email})
        assert signup_res.status_code == 200
        signup_data = signup_res.json()
        assert signup_data["email"] == email
        assert "mailinator.com" in signup_data["mailinator_url"]
        # Secure: activation token is NEVER leaked in the HTTP response
        assert "activation_link" not in signup_data

    # Token arrives strictly via the dispatched email
    assert len(captured_tokens) == 1
    token = captured_tokens[0]

    # Step 2: User sets password from email link
    set_pass_res = await client.post(
        "/api/v1/auth/set-password",
        json={"token": token, "password": "SecurePassword123!"},
    )
    assert set_pass_res.status_code == 200
    token_data = set_pass_res.json()
    assert "access_token" in token_data

    # Step 3: Verify the user is now active and authenticated
    me_res = await client.get(
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {token_data['access_token']}"},
    )
    assert me_res.status_code == 200
    assert me_res.json()["email"] == email
    assert me_res.json()["is_active"] is True

