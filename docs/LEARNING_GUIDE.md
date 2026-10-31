# KnowledgeAI Python & Engineering Mastery Guide

Welcome! KnowledgeAI is designed both as a production-grade full-stack RAG assistant and as an intensive, practical learning platform for mastering modern Python. This guide breaks down essential concepts, shows where each appears in the actual source code, and gives you hands-on exercises to deepen your understanding.

---

## 1. Type Hints & Modern Python 3.12+ Syntax

### Concept Explanation
Modern Python is statically analyzable and expressive. Instead of relying on guesswork, type hints (`str | None`, `list[float]`, `dict[str, Any]`) document function contracts, prevent bugs, and allow tools like `mypy` and IDEs to catch errors before code executes.

In Python 3.10+, union syntax `str | None` replaces `Optional[str]`, and built-in generics `list[str]` replace `typing.List[str]`.

### Where It Appears in KnowledgeAI
- [`backend/app/ai/base.py`](file:///c:/Projects/knowledge-ai/backend/app/ai/base.py): Look at `generate_chat_response` and `embed_documents`. Notice how parameter types and return types are strictly typed with domain models (`NormalizedChatResponse`, `list[list[float]]`).
- [`backend/app/core/config.py`](file:///c:/Projects/knowledge-ai/backend/app/core/config.py): Look at `ProviderType = Literal["openai", "gemini", "ollama"]`. `Literal` restricts string values to a closed set of valid options.

### Practice Exercise
Write a function `filter_high_scores(scores: list[float], threshold: float = 0.7) -> list[float]` using modern Python 3.12 syntax. Add type hints and test what happens when invalid types are passed.

---

## 2. Pydantic v2 & Configuration Management

### Concept Explanation
Pydantic is Python's leading data validation library. It validates inputs at the boundary (e.g. HTTP payloads, environment variables) and coerces them into strongly-typed objects. If an input is invalid, Pydantic immediately returns structured, human-readable errors instead of crashing deeper in the application.

### Where It Appears in KnowledgeAI
- [`backend/app/core/config.py`](file:///c:/Projects/knowledge-ai/backend/app/core/config.py): `Settings(BaseSettings)` reads values from `.env`, validates numbers and URLs, and automatically parses JSON lists for `CORS_ORIGINS`.
- [`backend/app/schemas/auth.py`](file:///c:/Projects/knowledge-ai/backend/app/schemas/auth.py): Look at `@field_validator("email")`. Notice how it automatically strips whitespace and normalizes email casing to lowercase.

### Practice Exercise
Add a new validator to `UserRegisterRequest` in `backend/app/schemas/auth.py` that verifies the password contains at least one uppercase letter and at least one digit.

---

## 3. Asynchronous I/O (`async` / `await`)

### Concept Explanation
Standard Python code is synchronous (blocking): when a database query or network request is executing, the CPU sits idle waiting for a response.
With `asyncio`, Python uses a single-threaded cooperative event loop. When a task hits an `await` point (such as waiting for PostgreSQL or Qdrant), it yields control, allowing the event loop to process other incoming HTTP requests concurrently.

### Where It Appears in KnowledgeAI
- [`backend/app/db/session.py`](file:///c:/Projects/knowledge-ai/backend/app/db/session.py): Look at `async def get_db_session() -> AsyncGenerator[AsyncSession, None]`. Notice `async with async_session_factory() as session:`.
- [`backend/app/services/rag_service.py`](file:///c:/Projects/knowledge-ai/backend/app/services/rag_service.py): Look at `async def execute_rag(...)`. Notice how it awaits embedding generation, vector search, and LLM chat generation without blocking the server.

### Practice Exercise
Explain the difference between `time.sleep(2)` and `await asyncio.sleep(2)`. What happens to other users if someone executes `time.sleep(10)` inside a FastAPI endpoint?

---

## 4. FastAPI Dependency Injection (`Depends`)

### Concept Explanation
Dependency Injection (DI) is a software design pattern where a component receives its dependencies from an external assembler rather than creating them internally. In FastAPI, `Depends(...)` enables composition, eliminates global state, and makes testing effortless by allowing test suites to override dependencies (e.g. replacing the real database with a test session).

### Where It Appears in KnowledgeAI
- [`backend/app/api/deps.py`](file:///c:/Projects/knowledge-ai/backend/app/api/deps.py): Look at `get_current_user`. It extracts the bearer token, validates the JWT, and loads the user from the database.
- [`backend/app/api/v1/documents.py`](file:///c:/Projects/knowledge-ai/backend/app/api/v1/documents.py): Every document route declares `current_user: User = Depends(get_current_user)` and `session: AsyncSession = Depends(get_db_session)`.

### Practice Exercise
Look at `backend/tests/conftest.py`. Observe how `app.dependency_overrides[get_db_session] = override_get_db` swaps the PostgreSQL connection with an isolated in-memory test database without altering a single line of backend code.

---

## 5. SQLAlchemy 2.0 Async ORM & Alembic Migrations

### Concept Explanation
SQLAlchemy 2.0 separates declarative models (`Mapped`, `mapped_column`) from query execution (`select(User).where(...)`). Migrations with Alembic track schema changes over time in version-controlled migration scripts, guaranteeing that staging and production environments stay in sync without manual SQL execution.

### Where It Appears in KnowledgeAI
- [`backend/app/models/user.py`](file:///c:/Projects/knowledge-ai/backend/app/models/user.py) and [`document.py`](file:///c:/Projects/knowledge-ai/backend/app/models/document.py): Notice `Mapped[uuid.UUID]`, foreign key cascades, and relationships.
- [`backend/alembic/versions/001_initial_schema.py`](file:///c:/Projects/knowledge-ai/backend/alembic/versions/001_initial_schema.py): The initial schema migration creating users, documents, chunks, conversations, and messages tables with explicit foreign keys and indexes.

### Practice Exercise
Inspect `backend/alembic/env.py`. How does Alembic discover all ORM models for autogeneration? Why is `from app.models import ...` necessary?

---

## 6. Background Processing, Celery & Idempotency

### Concept Explanation
CPU-heavy or network-heavy operations (extracting 50-page PDFs, embedding 200 chunks, upserting to vector stores) should never block HTTP request threads. Background task queues (Celery + Redis) offload this work.
**Idempotency** ensures that if a background task is executed multiple times (e.g. due to network retries), the end result is identical without creating duplicate chunks or orphan vectors.

### Where It Appears in KnowledgeAI
- [`backend/app/workers/document_tasks.py`](file:///c:/Projects/knowledge-ai/backend/app/workers/document_tasks.py): Notice the idempotency check:
  `if doc.status == "completed": return True`. Notice also the rollback and cleanup logic if extraction or embedding fails.
- [`backend/app/services/document_service.py`](file:///c:/Projects/knowledge-ai/backend/app/services/document_service.py): Uses SHA-256 checksums to detect and reject duplicate uploads.

### Practice Exercise
If a Celery worker dies midway through upserting vectors, what happens when the retry task runs? Why does `vector_service.delete_by_document` ensure no duplicate vectors exist in Qdrant?

---

## 7. Provider Decoupling & Factory Pattern

### Concept Explanation
The Factory pattern abstracts object creation behind a unified interface. By decoupling the Chat interface (`ChatProvider`) from the Embedding interface (`EmbeddingProvider`), the application can change AI vendors (OpenAI $\leftrightarrow$ Gemini $\leftrightarrow$ Ollama) via environment variables without touching business logic.

### Where It Appears in KnowledgeAI
- [`backend/app/ai/base.py`](file:///c:/Projects/knowledge-ai/backend/app/ai/base.py): Abstract base classes defining the protocol.
- [`backend/app/ai/factory.py`](file:///c:/Projects/knowledge-ai/backend/app/ai/factory.py): `AIProviderFactory.get_chat_provider()` and `AIProviderFactory.get_embedding_provider()`.

### Practice Exercise
Inspect `backend/tests/unit/test_ai_factory.py`. Run the test and observe how missing API keys produce immediate, clear exceptions rather than failing silently during inference.

---

## 8. Retrieval-Augmented Generation (RAG) & Citation Verification

### Concept Explanation
Large Language Models have static knowledge and can hallucinate. RAG enhances prompts with relevant context retrieved from a vector database. However, LLMs might still hallucinate sources. In KnowledgeAI, **application-level citation validation** parses bracketed tags (`[Chunk 0]`), matches them against the actual retrieved database chunks, extracts real page numbers, and rejects fabricated references.

### Where It Appears in KnowledgeAI
- [`backend/app/services/rag_service.py`](file:///c:/Projects/knowledge-ai/backend/app/services/rag_service.py): Look at `_verify_citations(...)` and `RAG_SYSTEM_PROMPT`. Notice how retrieved context is treated as untrusted user data to protect against prompt injection.

### Practice Exercise
Review `backend/tests/unit/test_rag_verification.py`. See how `test_verify_citations_rejects_hallucinated_ids` ensures the model cannot invent chunk numbers.

---

## 9. Security & Isolation

### Concept Explanation
Multi-tenant security requires **owner-level authorization** at every layer. Knowing an entity's UUID is never sufficient; queries must explicitly include `where(Document.owner_id == current_user.id)` and Qdrant filters must include `MatchValue(key="owner_id", value=current_user.id)`.

### Where It Appears in KnowledgeAI
- [`backend/app/repositories/document_repository.py`](file:///c:/Projects/knowledge-ai/backend/app/repositories/document_repository.py)
- [`backend/tests/integration/test_documents_api.py`](file:///c:/Projects/knowledge-ai/backend/tests/integration/test_documents_api.py): Look at `test_cross_user_document_isolation` to see how unauthorized reads and deletes are rejected with 404 Not Found.

