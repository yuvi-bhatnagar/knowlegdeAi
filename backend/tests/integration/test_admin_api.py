import pytest
from httpx import AsyncClient

from app.core.runtime import RuntimeSettings
from app.db.seed import seed_admin_and_settings, ADMIN_EMAIL
from app.models.user import User


@pytest.mark.asyncio
async def test_admin_access_forbidden_for_regular_user(
    client: AsyncClient,
    auth_headers: dict[str, str],
):
    """Verify regular non-admin users cannot access admin endpoints."""
    res = await client.get("/api/v1/admin/overview", headers=auth_headers)
    assert res.status_code == 403
    assert "administrator privileges required" in res.json()["detail"].lower()


@pytest.mark.asyncio
async def test_admin_overview_success(
    client: AsyncClient,
    admin_auth_headers: dict[str, str],
):
    """Verify admin can retrieve overview metrics and infrastructure status."""
    res = await client.get("/api/v1/admin/overview", headers=admin_auth_headers)
    assert res.status_code == 200
    data = res.json()
    assert "users" in data
    assert "infrastructure" in data
    assert data["infrastructure"]["status"] == "ready"
    assert "chat" in data


@pytest.mark.asyncio
async def test_admin_settings_and_runtime_ai_provider_switching(
    client: AsyncClient,
    admin_auth_headers: dict[str, str],
):
    """Verify admin can inspect available AI providers and switch the active chat provider dynamically."""
    # 1. Fetch current runtime settings
    res = await client.get("/api/v1/admin/settings", headers=admin_auth_headers)
    assert res.status_code == 200
    data = res.json()
    assert "active_chat_provider" in data
    assert "providers" in data
    assert len(data["providers"]) == 3  # gemini, openai, ollama

    # 2. Switch provider to openai
    patch_res = await client.patch(
        "/api/v1/admin/settings/ai-chat-provider",
        headers=admin_auth_headers,
        json={"provider": "openai"},
    )
    assert patch_res.status_code == 200
    assert patch_res.json()["active_chat_provider"] == "openai"
    assert RuntimeSettings.get_chat_provider() == "openai"

    # 3. Switch back to gemini
    patch_res2 = await client.patch(
        "/api/v1/admin/settings/ai-chat-provider",
        headers=admin_auth_headers,
        json={"provider": "gemini"},
    )
    assert patch_res2.status_code == 200
    assert patch_res2.json()["active_chat_provider"] == "gemini"
    assert RuntimeSettings.get_chat_provider() == "gemini"


@pytest.mark.asyncio
async def test_admin_user_management(
    client: AsyncClient,
    admin_auth_headers: dict[str, str],
    admin_user: User,
    test_user: User,
):
    """Verify admin can list users and toggle user activation status."""
    # 1. List users
    res = await client.get("/api/v1/admin/users", headers=admin_auth_headers)
    assert res.status_code == 200
    users_data = res.json()
    assert users_data["total"] >= 2
    emails = [u["email"] for u in users_data["items"]]
    assert test_user.email in emails
    assert admin_user.email in emails

    # 2. Deactivate test_user
    toggle_res = await client.patch(
        f"/api/v1/admin/users/{test_user.id}/status",
        headers=admin_auth_headers,
        json={"is_active": False},
    )
    assert toggle_res.status_code == 200
    assert toggle_res.json()["is_active"] is False

    # 3. Reactivate test_user
    toggle_res2 = await client.patch(
        f"/api/v1/admin/users/{test_user.id}/status",
        headers=admin_auth_headers,
        json={"is_active": True},
    )
    assert toggle_res2.status_code == 200
    assert toggle_res2.json()["is_active"] is True

    # 4. Admin cannot deactivate themselves
    self_res = await client.patch(
        f"/api/v1/admin/users/{admin_user.id}/status",
        headers=admin_auth_headers,
        json={"is_active": False},
    )
    assert self_res.status_code in (400, 422)


@pytest.mark.asyncio
async def test_admin_login_with_seeded_credentials(client: AsyncClient, admin_user: User):
    """Verify admin_knowledge_36@knowledge.ai can authenticate with Test!234 and has admin role."""
    res = await client.post(
        "/api/v1/auth/login",
        json={"email": ADMIN_EMAIL, "password": "Test!234"},
    )
    assert res.status_code == 200
    token = res.json()["access_token"]

    me_res = await client.get(
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert me_res.status_code == 200
    me = me_res.json()
    assert me["email"] == ADMIN_EMAIL
    assert me["is_superuser"] is True
    assert me["role"] == "admin"
