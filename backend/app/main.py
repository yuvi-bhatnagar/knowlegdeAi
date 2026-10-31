import time
import uuid
from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.api.v1.router import api_router
from app.core.config import settings
from app.core.exceptions import AppException
from app.core.logging import logger


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Application startup and shutdown events."""
    logger.info("Initializing KnowledgeAI application...", extra={"environment": settings.ENVIRONMENT})
    # Ensure storage directory exists
    settings.storage_path.mkdir(parents=True, exist_ok=True)

    # Seed default administrator and runtime settings
    try:
        from app.db.session import async_session_factory
        from app.db.seed import seed_admin_and_settings
        async with async_session_factory() as session:
            await seed_admin_and_settings(session)
    except Exception as exc:
        logger.warning(f"DB startup seeding bypassed (table may be migrating): {exc}")

    yield
    logger.info("Shutting down KnowledgeAI application...")


app = FastAPI(
    title=settings.APP_NAME,
    version="0.1.0",
    description="KnowledgeAI: Full-Stack RAG Knowledge Assistant with Multi-Provider Support.",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
)

# CORS Configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS if settings.CORS_ORIGINS != ["*"] else ["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def request_context_middleware(request: Request, call_next):
    """Assigns unique request ID and logs request latency."""
    request_id = request.headers.get("X-Request-ID") or str(uuid.uuid4())
    request.state.request_id = request_id
    start_time = time.time()

    response = await call_next(request)

    process_time = (time.time() - start_time) * 1000
    response.headers["X-Request-ID"] = request_id
    response.headers["X-Process-Time-Ms"] = f"{process_time:.2f}"

    logger.info(
        f"{request.method} {request.url.path} completed with status {response.status_code} in {process_time:.2f}ms [req_id={request_id}]"
    )
    return response


@app.exception_handler(AppException)
async def app_exception_handler(request: Request, exc: AppException) -> JSONResponse:
    """Handle custom application exceptions and return standardized error format."""
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": {
                "code": exc.code,
                "message": exc.message,
                "details": exc.details,
            }
        },
    )


@app.exception_handler(Exception)
async def generic_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """Safely catch unhandled internal exceptions without leaking sensitive server internals."""
    req_id = getattr(request.state, "request_id", "unknown")
    logger.exception(f"Unhandled exception on request {req_id}: {str(exc)}")
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "error": {
                "code": "INTERNAL_SERVER_ERROR",
                "message": "An unexpected server error occurred. Please try again later.",
                "request_id": req_id,
            }
        },
    )


# Register API v1 routes
app.include_router(api_router, prefix=settings.API_V1_STR)
