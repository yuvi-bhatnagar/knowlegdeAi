import uuid
import pytest
from httpx import AsyncClient
from unittest.mock import AsyncMock, patch
from app.ai.base import NormalizedChatResponse
from app.schemas.chat import Citation


@pytest.mark.asyncio
async def test_create_and_list_conversations(client: AsyncClient, auth_headers: dict[str, str]):
    # 1. Create conversation
    res = await client.post(
        "/api/v1/conversations",
        headers=auth_headers,
        json={"title": "Python Architecture Thread"},
    )
    assert res.status_code == 201
    conv_data = res.json()
    conv_id = conv_data["id"]
    assert conv_data["title"] == "Python Architecture Thread"

    # 2. List conversations
    list_res = await client.get("/api/v1/conversations", headers=auth_headers)
    assert list_res.status_code == 200
    list_json = list_res.json()
    assert list_json["total"] >= 1
    assert any(c["id"] == conv_id for c in list_json["items"])

    # 3. Rename conversation
    patch_res = await client.patch(
        f"/api/v1/conversations/{conv_id}",
        headers=auth_headers,
        json={"title": "Updated Thread Title"},
    )
    assert patch_res.status_code == 200
    assert patch_res.json()["title"] == "Updated Thread Title"

    # 4. Delete conversation
    del_res = await client.delete(f"/api/v1/conversations/{conv_id}", headers=auth_headers)
    assert del_res.status_code == 204

    # 5. Verify deletion
    get_res = await client.get(f"/api/v1/conversations/{conv_id}", headers=auth_headers)
    assert get_res.status_code == 404


@pytest.mark.asyncio
async def test_cross_user_conversation_isolation(client: AsyncClient, auth_headers: dict[str, str]):
    # Register attacker
    await client.post(
        "/api/v1/auth/register",
        json={"email": "conv_attacker@example.com", "password": "Password123!"},
    )
    login_res = await client.post(
        "/api/v1/auth/login",
        json={"email": "conv_attacker@example.com", "password": "Password123!"},
    )
    attacker_headers = {"Authorization": f"Bearer {login_res.json()['access_token']}"}

    # User 1 creates conversation
    create_res = await client.post(
        "/api/v1/conversations",
        headers=auth_headers,
        json={"title": "Confidential Chat"},
    )
    conv_id = create_res.json()["id"]

    # Attacker tries to read -> 404
    att_res = await client.get(f"/api/v1/conversations/{conv_id}", headers=attacker_headers)
    assert att_res.status_code == 404

    # Attacker tries to delete -> 404
    att_del = await client.delete(f"/api/v1/conversations/{conv_id}", headers=attacker_headers)
    assert att_del.status_code == 404


@pytest.mark.asyncio
async def test_chat_endpoint_grounded_answer(client: AsyncClient, auth_headers: dict[str, str]):
    # Mock RAGService.execute_rag to return controlled answer and citation
    dummy_doc_id = uuid.uuid4()
    mock_citation = Citation(
        document_id=dummy_doc_id,
        filename="rag_specs.txt",
        page_number=1,
        chunk_index=0,
        excerpt="KnowledgeAI enforces citation verification.",
        score=0.92,
    )

    with patch(
        "app.services.rag_service.RAGService.execute_rag",
        new_callable=AsyncMock,
    ) as mock_rag:
        mock_rag.return_value = (
            "KnowledgeAI enforces citations [Chunk 0].",
            [mock_citation],
            "gpt-4o-mini",
            False,
        )

        chat_payload = {
            "question": "How does KnowledgeAI handle citations?",
        }
        res = await client.post("/api/v1/chat", headers=auth_headers, json=chat_payload)
        assert res.status_code == 200
        data = res.json()
        assert "KnowledgeAI enforces citations" in data["answer"]
        assert len(data["citations"]) == 1
        assert data["citations"][0]["filename"] == "rag_specs.txt"
        assert "conversation_id" in data
        assert "message_id" in data
        assert data["insufficient_evidence"] is False

        # Verify message history contains both user and assistant messages
        conv_id = data["conversation_id"]
        msg_res = await client.get(f"/api/v1/conversations/{conv_id}/messages", headers=auth_headers)
        assert msg_res.status_code == 200
        messages = msg_res.json()
        assert len(messages) == 2
        assert messages[0]["role"] == "user"
        assert messages[0]["content"] == "How does KnowledgeAI handle citations?"
        assert messages[1]["role"] == "assistant"
        assert "KnowledgeAI enforces citations" in messages[1]["content"]

