# KnowledgeAI - Personal AI Knowledge Assistant

KnowledgeAI is a production-style, runnable full-stack application that enables users to register, ingest documents (PDF, TXT, Markdown), ask questions grounded strictly in their own documents using Retrieval-Augmented Generation (RAG), and receive answers with verified source citations.

---

## 🚀 Key Features

- **Document Ingestion & Parsing**: Native text and page extraction from PDF, TXT, and Markdown files using PyMuPDF. Detects image-only/scanned PDFs without OCR text.
- **Asynchronous Processing**: Background document extraction, chunking, and vector indexing using Redis and Celery.
- **Decoupled AI Providers**: Switch between **OpenAI**, **Google Gemini**, and local **Ollama** via environment variables without modifying code. Chat and Embeddings are independently configurable.
- **Grounded RAG with Verified Citations**: Application-level citation validation verifies source references against retrieved database chunks and page numbers, rejecting hallucinated IDs.
- **Persistent Conversations**: Complete thread management, renaming, deletion, and message history with token usage tracking.
- **Multi-Tenant Security & Email Verification**: Strict per-user isolation on all database queries and vector searches. Argon2id password hashing, HS256 JWT authentication, and Mailinator-compatible email verification with secure password creation tokens.
- **Responsive React Frontend**: Modern dark-mode interface built with React 18, TypeScript, and Vite.
- **Comprehensive Documentation**: Complete architecture guides, provider switching documentation, API examples, and an in-depth Python learning guide.

---

## 🛠️ Tech Stack

- **Backend**: Python 3.12+, FastAPI, Pydantic v2, pydantic-settings
- **Database**: PostgreSQL 16, SQLAlchemy 2.0 Async, Alembic
- **Vector Database**: Qdrant
- **Task Queue & Caching**: Celery, Redis
- **Document Processing**: PyMuPDF (`pymupdf`)
- **AI SDKs**: Official `openai`, `google-genai`, and local `ollama` HTTP adapter
- **Security**: Argon2 (`argon2-cffi`), JWT (`pyjwt`)
- **Frontend**: React 18, TypeScript, Vite, Lucide Icons
- **Testing**: pytest, pytest-asyncio, HTTPX

---

## 📦 Quick Start (Docker Compose)

The easiest way to start the complete stack (PostgreSQL, Redis, Qdrant, Backend, Celery Worker, Frontend):

1. **Clone & Configure Environment**:
   ```bash
   cp .env.example .env
   ```
   Edit `.env` to configure your API keys (e.g. `OPENAI_API_KEY` or `GEMINI_API_KEY`).

2. **Start All Services**:
   ```bash
   docker compose up --build
   ```

3. **Access the Application**:
   - **Frontend**: [http://localhost:5173](http://localhost:5173)
   - **Backend API & Swagger Docs**: [http://localhost:8000/docs](http://localhost:8000/docs)
   - **Qdrant Dashboard**: [http://localhost:6333/dashboard](http://localhost:6333/dashboard)

### 🔑 Default Administrator Credentials
On startup, KnowledgeAI automatically seeds the default administrator account:
- **Email**: `admin_knowledge_36@knowledge.ai`
- **Password**: `Test!234`
- **Privileges**: Access to the dedicated **Admin Console** with dynamic runtime AI provider switching (Gemini, OpenAI, Ollama), user management, and infrastructure telemetry.

---

## 💻 Local Development Setup

### 1. Backend Setup
```bash
# Create virtual environment and activate
python -m venv .venv
# Windows:
.\.venv\Scripts\Activate.ps1
# Linux/macOS:
source .venv/bin/activate

# Install dependencies
pip install -r backend/requirements.txt

# Run database migrations
alembic -c backend/alembic.ini upgrade head

# Start development server
uvicorn app.main:app --app-dir backend --reload --port 8000
```

### 2. Celery Worker (in a separate terminal)
```bash
celery -A app.workers.celery_app.celery_app worker --app-dir backend --loglevel=info
```

### 3. Frontend Setup (in a separate terminal)
```bash
cd frontend
npm install
npm run dev
```

---

## 🧪 Running Tests

The test suite includes 44 unit and integration tests covering security, chunking, AI factory, provider selection, RAG citation validation, document ingestion, cross-user isolation, email-first registration, and administrative controls with runtime model switching. Unit tests run completely offline without requiring paid API keys:

```bash
# Run all tests
$env:PYTHONPATH="backend"  # Windows PowerShell
pytest backend/tests -v
```

---

## 🔄 Provider Switching

Switch providers at any time in `.env`:

```env
# Use OpenAI for Chat and Gemini for Embeddings
AI_CHAT_PROVIDER=openai
AI_EMBEDDING_PROVIDER=gemini

OPENAI_API_KEY=sk-proj-...
GEMINI_API_KEY=AIzaSy...
```

See [`docs/AI_PROVIDERS.md`](docs/AI_PROVIDERS.md) for full details on model compatibility, dimensions, and versioned vector collections.

---

## 📚 Documentation Links

- [System Architecture & Data Flows](docs/ARCHITECTURE.md)
- [AI Provider Configuration Guide](docs/AI_PROVIDERS.md)
- [Email Provider Configuration Guide (Mailinator & SendGrid)](docs/EMAIL_PROVIDERS.md)
- [API Examples & cURL Requests](docs/API_EXAMPLES.md)
- [Python Learning Guide & Code Walkthrough](docs/LEARNING_GUIDE.md)

---

## ⚖️ License
MIT License. Created for education and production-style engineering mastery.

