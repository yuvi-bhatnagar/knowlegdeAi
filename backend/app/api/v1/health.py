from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession
import httpx
import redis.asyncio as aioredis

from app.core.config import settings
from app.db.session import get_db_session

router = APIRouter(prefix="/health", tags=["Health"])


@router.get("/live")
async def health_live() -> dict[str, str]:
    """Liveness probe: returns 200 if the FastAPI application process is alive."""
    return {"status": "ok"}


@router.get("/ready")
async def health_ready(
    session: AsyncSession = Depends(get_db_session),
) -> dict:
    """Readiness probe: validates database, cache, vector store, and AI provider configuration."""
    checks = {
        "database": False,
        "redis": False,
        "qdrant": False,
        "ai_diagnostics": settings.validate_provider_configuration(),
    }

    # 1. Database check
    try:
        result = await session.execute(text("SELECT 1"))
        if result.scalar() == 1:
            checks["database"] = True
    except Exception as exc:
        checks["database_error"] = str(exc)

    # 2. Redis check
    try:
        r = aioredis.from_url(settings.REDIS_URL, socket_connect_timeout=2.0)
        await r.ping()
        await r.aclose()
        checks["redis"] = True
    except Exception as exc:
        checks["redis_error"] = str(exc)

    # 3. Qdrant check
    try:
        async with httpx.AsyncClient(timeout=2.0) as client:
            headers = {}
            if settings.QDRANT_API_KEY:
                headers["api-key"] = settings.QDRANT_API_KEY
            q_res = await client.get(f"http://{settings.QDRANT_HOST}:{settings.QDRANT_PORT}/readyz", headers=headers)
            checks["qdrant"] = (q_res.status_code == 200)
    except Exception as exc:
        checks["qdrant_error"] = str(exc)

    is_ready = checks["database"]
    return {
        "status": "ready" if is_ready else "degraded",
        "checks": checks,
    }
