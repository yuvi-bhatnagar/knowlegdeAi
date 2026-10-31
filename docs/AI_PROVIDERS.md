# AI Provider Switching & Configuration Guide

KnowledgeAI decouples **Chat Generation** from **Embedding Generation**, allowing you to mix and match providers or switch completely without modifying application code.

## 1. Supported Providers & Models

| Provider | Supported Roles | Maintained SDK | Default Chat Model | Default Embedding Model | Dimensions |
|---|---|---|---|---|---|
| **OpenAI** | Chat & Embeddings | `openai` (official) | `gpt-4o-mini` | `text-embedding-3-small` | 1536 |
| **Google Gemini** | Chat & Embeddings | `google-genai` (official) | `gemini-1.5-flash` | `gemini-embedding-001` | 3072 |
| **Ollama** (Local) | Chat & Embeddings | `httpx` (REST API) | `llama3.2` | `nomic-embed-text` | 768 |

---

## 2. Configuration Examples

All provider configuration is managed in `.env`. After modifying `.env`, restart the backend and worker services:
```bash
docker compose restart backend celery_worker
```

### Scenario A: Pure OpenAI Setup
```env
AI_CHAT_PROVIDER=openai
AI_EMBEDDING_PROVIDER=openai

OPENAI_API_KEY=sk-proj-your-openai-api-key-here
OPENAI_CHAT_MODEL=gpt-4o-mini
OPENAI_EMBEDDING_MODEL=text-embedding-3-small
```

### Scenario B: Pure Google Gemini Setup
```env
AI_CHAT_PROVIDER=gemini
AI_EMBEDDING_PROVIDER=gemini

GEMINI_API_KEY=AIzaSy-your-gemini-api-key-here
GEMINI_CHAT_MODEL=gemini-1.5-flash
GEMINI_EMBEDDING_MODEL=gemini-embedding-001
```

### Scenario C: Mixed Mode (Gemini Chat + OpenAI Embeddings)
You can take advantage of Gemini's cost efficiency or context window for chat, while using OpenAI's embeddings:
```env
AI_CHAT_PROVIDER=gemini
AI_EMBEDDING_PROVIDER=openai

GEMINI_API_KEY=AIzaSy-your-gemini-api-key-here
GEMINI_CHAT_MODEL=gemini-1.5-flash

OPENAI_API_KEY=sk-proj-your-openai-api-key-here
OPENAI_EMBEDDING_MODEL=text-embedding-3-small
```

### Scenario D: Local Offline Ollama Setup
Run locally without third-party API keys:
```env
AI_CHAT_PROVIDER=ollama
AI_EMBEDDING_PROVIDER=ollama

OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_CHAT_MODEL=llama3.2
OLLAMA_EMBEDDING_MODEL=nomic-embed-text
```

---

## 3. Embedding Compatibility & Index Versioning

Vector databases require that all stored vectors and search query vectors reside in the **same vector space** and have the **exact same number of dimensions**.

### Collection Naming Scheme
KnowledgeAI automatically derives Qdrant collection names by combining prefix, sanitized model name, and dimensions:
$$\text{Collection Name} = \text{prefix}\_\text{model}\_\text{dimension}$$

Examples:
- `knowledge_ai_text_embedding_3_small_1536`
- `knowledge_ai_text_embedding_004_768`
- `knowledge_ai_nomic_embed_text_768`

### Safe Switching Behavior
1. **Changing Chat Provider**: If you switch `AI_CHAT_PROVIDER` (e.g. from OpenAI to Gemini) while keeping `AI_EMBEDDING_PROVIDER` unchanged, **no re-indexing is required**! All existing documents and vectors continue to work seamlessly.
2. **Changing Embedding Provider**: If you change `AI_EMBEDDING_PROVIDER`, KnowledgeAI targets the new collection version. It detects dimensionality mismatches and prevents mixing incompatible vector spaces. Re-upload or trigger the `/retry` endpoint on documents to build the new index version. Old indices are preserved until the new index succeeds.

---

## 4. Diagnostics & Health Verification

Check provider readiness and diagnostics without exposing secrets:
```bash
curl -X GET http://localhost:8000/api/v1/health/ready
```

Sample JSON response:
```json
{
  "status": "ready",
  "checks": {
    "database": true,
    "redis": true,
    "qdrant": true,
    "ai_diagnostics": {
      "chat_provider": "openai",
      "embedding_provider": "openai",
      "chat_ready": true,
      "embedding_ready": true,
      "errors": []
    }
  }
}
```
If an API key is missing, `ai_diagnostics` reports explicit instructions in `errors` without ever leaking credentials.

