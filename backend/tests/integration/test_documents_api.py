import io
import uuid
import pytest
from httpx import AsyncClient
from app.models.user import User
from app.core.security import get_password_hash, create_access_token
from tests.conftest import TestingSessionLocal


@pytest.mark.asyncio
async def test_upload_document_success(client: AsyncClient, auth_headers: dict[str, str]):
    file_content = b"KnowledgeAI is an intelligent RAG system that answers questions based on user documents."
    files = {"file": ("architecture.txt", io.BytesIO(file_content), "text/plain")}

    response = await client.post("/api/v1/documents/upload", headers=auth_headers, files=files)
    assert response.status_code == 201
    data = response.json()
    assert "id" in data
    assert data["original_filename"] == "architecture.txt"
    assert data["status"] == "uploaded"


@pytest.mark.asyncio
async def test_upload_document_duplicate_detected(client: AsyncClient, auth_headers: dict[str, str]):
    file_content = b"Duplicate file content for test."
    files1 = {"file": ("dup.txt", io.BytesIO(file_content), "text/plain")}
    res1 = await client.post("/api/v1/documents/upload", headers=auth_headers, files=files1)
    assert res1.status_code == 201

    # Second upload with identical content should fail with 409
    files2 = {"file": ("dup_copy.txt", io.BytesIO(file_content), "text/plain")}
    res2 = await client.post("/api/v1/documents/upload", headers=auth_headers, files=files2)
    assert res2.status_code == 409
    assert res2.json()["error"]["code"] == "ALREADY_EXISTS"


@pytest.mark.asyncio
async def test_list_and_get_document(client: AsyncClient, auth_headers: dict[str, str]):
    file_content = b"Doc for listing and retrieving."
    files = {"file": ("test_doc.md", io.BytesIO(file_content), "text/markdown")}
    upload_res = await client.post("/api/v1/documents/upload", headers=auth_headers, files=files)
    assert upload_res.status_code == 201
    doc_id = upload_res.json()["id"]

    # List documents
    list_res = await client.get("/api/v1/documents", headers=auth_headers)
    assert list_res.status_code == 200
    list_data = list_res.json()
    assert list_data["total"] >= 1
    assert any(d["id"] == doc_id for d in list_data["items"])

    # Get single document
    get_res = await client.get(f"/api/v1/documents/{doc_id}", headers=auth_headers)
    assert get_res.status_code == 200
    assert get_res.json()["id"] == doc_id


@pytest.mark.asyncio
async def test_cross_user_document_isolation(client: AsyncClient, auth_headers: dict[str, str]):
    # Register and authenticate second user via API
    reg_res = await client.post(
        "/api/v1/auth/register",
        json={"email": "attacker@example.com", "password": "AttackerPass123!"},
    )
    assert reg_res.status_code == 201

    login_res = await client.post(
        "/api/v1/auth/login",
        json={"email": "attacker@example.com", "password": "AttackerPass123!"},
    )
    assert login_res.status_code == 200
    second_user_headers = {"Authorization": f"Bearer {login_res.json()['access_token']}"}

    # User 1 uploads document
    files = {"file": ("private.txt", io.BytesIO(b"Confidential user 1 content"), "text/plain")}
    upload_res = await client.post("/api/v1/documents/upload", headers=auth_headers, files=files)
    assert upload_res.status_code == 201
    doc_id = upload_res.json()["id"]

    # User 2 tries to GET document -> should return 404 (not found in user 2's scope)
    get_res = await client.get(f"/api/v1/documents/{doc_id}", headers=second_user_headers)
    assert get_res.status_code == 404

    # User 2 tries to DELETE document -> should return 404
    del_res = await client.delete(f"/api/v1/documents/{doc_id}", headers=second_user_headers)
    assert del_res.status_code == 404

    # User 1 deletes document -> should return 204
    own_del = await client.delete(f"/api/v1/documents/{doc_id}", headers=auth_headers)
    assert own_del.status_code == 204
