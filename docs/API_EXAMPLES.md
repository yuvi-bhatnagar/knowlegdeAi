# KnowledgeAI API Examples (cURL & Responses)

Base URL: `http://localhost:8000/api/v1`

---

## 1. Authentication & Email-First Signup

### 1.1 Email-Only Signup (Mailinator-Compatible)
Initiates account registration by email. Dispatches a signed activation link. For `@mailinator.com` addresses, returns the public inbox link for easy zero-config testing:
```bash
curl -X POST http://localhost:8000/api/v1/auth/signup \
  -H "Content-Type: application/json" \
  -d '{
    "email": "student123@mailinator.com"
  }'
```
**Response (200 OK):**
```json
{
  "message": "Activation email dispatched. Please verify your email to set your password.",
  "email": "student123@mailinator.com",
  "mailinator_url": "https://www.mailinator.com/v4/public/inboxes.jsp?to=student123"
}
```

### 1.2 Set Password & Activate Account
Used by the user when clicking the emailed link. Sets their password, activates the account, and returns JWT tokens:
```bash
curl -X POST http://localhost:8000/api/v1/auth/set-password \
  -H "Content-Type: application/json" \
  -d '{
    "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
    "password": "StrongPassword123!"
  }'
```
**Response (200 OK):**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "expires_in_seconds": 86400
}
```

### 1.3 Direct Register (Programmatic)
```bash
curl -X POST http://localhost:8000/api/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "email": "engineer@example.com",
    "password": "StrongPassword123!"
  }'
```
**Response (201 Created):**
```json
{
  "id": "e4b29bb8-55fc-4235-90df-a6d17bcecf3b",
  "email": "engineer@example.com",
  "is_active": true,
  "created_at": "2026-10-30T08:00:00Z",
  "updated_at": "2026-10-30T08:00:00Z"
}
```

### 1.4 Login & Receive Token
```bash
curl -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "email": "engineer@example.com",
    "password": "StrongPassword123!"
  }'
```
**Response (200 OK):**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "expires_in_seconds": 86400
}
```

---

## 2. Documents

### 2.1 Upload Document (PDF / TXT / Markdown)
```bash
curl -X POST http://localhost:8000/api/v1/documents/upload \
  -H "Authorization: Bearer <YOUR_TOKEN>" \
  -F "file=@./sample_guide.pdf"
```
**Response (201 Created):**
```json
{
  "id": "76d1e4e2-8e10-41bf-a338-e6b8c830d5ee",
  "original_filename": "sample_guide.pdf",
  "status": "uploaded",
  "message": "Document uploaded successfully and queued for indexing."
}
```

### 2.2 List Uploaded Documents
```bash
curl -X GET "http://localhost:8000/api/v1/documents?page=1&page_size=20" \
  -H "Authorization: Bearer <YOUR_TOKEN>"
```
**Response (200 OK):**
```json
{
  "items": [
    {
      "id": "76d1e4e2-8e10-41bf-a338-e6b8c830d5ee",
      "original_filename": "sample_guide.pdf",
      "mime_type": "application/pdf",
      "file_size": 1048576,
      "checksum": "a3b2c1d0...",
      "status": "completed",
      "error_summary": null,
      "chunk_count": 18,
      "created_at": "2026-10-30T08:05:00Z",
      "updated_at": "2026-10-30T08:05:12Z"
    }
  ],
  "total": 1,
  "page": 1,
  "page_size": 20,
  "total_pages": 1
}
```

### 2.3 Delete Document
```bash
curl -X DELETE http://localhost:8000/api/v1/documents/76d1e4e2-8e10-41bf-a338-e6b8c830d5ee \
  -H "Authorization: Bearer <YOUR_TOKEN>"
```
**Response:** `204 No Content`

---

## 3. Chat & Conversations

### 3.1 Submit Question to RAG Engine
```bash
curl -X POST http://localhost:8000/api/v1/chat \
  -H "Authorization: Bearer <YOUR_TOKEN>" \
  -H "Content-Type: application/json" \
  -d '{
    "question": "What are the core principles of KnowledgeAI?",
    "conversation_id": null
  }'
```
**Response (200 OK):**
```json
{
  "answer": "KnowledgeAI adheres to a modular monolith architecture with strict separation of concerns, provider decoupling, and grounded responses [Chunk 0].",
  "conversation_id": "3b29c91f-0e12-40f6-9764-5853b0bc8c05",
  "message_id": "1e9f1a23-4567-4890-abcd-ef0123456789",
  "citations": [
    {
      "document_id": "76d1e4e2-8e10-41bf-a338-e6b8c830d5ee",
      "filename": "sample_guide.pdf",
      "page_number": 2,
      "chunk_index": 0,
      "excerpt": "KnowledgeAI adheres to a modular monolith architecture with strict separation of concerns...",
      "score": 0.89
    }
  ],
  "model_used": "gpt-4o-mini",
  "insufficient_evidence": false
}
```

### 3.2 List Conversation Messages
```bash
curl -X GET http://localhost:8000/api/v1/conversations/3b29c91f-0e12-40f6-9764-5853b0bc8c05/messages \
  -H "Authorization: Bearer <YOUR_TOKEN>"
```

---

## 4. Health Checks

### 4.1 Liveness
```bash
curl -X GET http://localhost:8000/api/v1/health/live
```
**Response (200 OK):**
```json
{"status": "ok"}
```

### 4.2 Readiness
```bash
curl -X GET http://localhost:8000/api/v1/health/ready
```

