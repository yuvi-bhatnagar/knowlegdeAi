from typing import Any


class AppException(Exception):
    """Base application exception with safe message and optional error code."""

    def __init__(self, message: str, status_code: int = 400, code: str = "BAD_REQUEST", details: Any = None):
        super().__init__(message)
        self.message = message
        self.status_code = status_code
        self.code = code
        self.details = details


class EntityNotFoundException(AppException):
    def __init__(self, entity_name: str, identifier: Any):
        super().__init__(
            message=f"{entity_name} with identifier '{identifier}' was not found.",
            status_code=404,
            code="NOT_FOUND",
        )


class EntityAlreadyExistsException(AppException):
    def __init__(self, message: str):
        super().__init__(message=message, status_code=409, code="ALREADY_EXISTS")


class AuthenticationException(AppException):
    def __init__(self, message: str = "Invalid authentication credentials."):
        super().__init__(message=message, status_code=401, code="UNAUTHORIZED")


class AuthorizationException(AppException):
    def __init__(self, message: str = "You do not have permission to access this resource."):
        super().__init__(message=message, status_code=403, code="FORBIDDEN")


class ValidationException(AppException):
    def __init__(self, message: str, details: Any = None):
        super().__init__(message=message, status_code=422, code="VALIDATION_ERROR", details=details)


class AIServiceException(AppException):
    """Exception raised during AI provider communication, generation, or embedding."""
    def __init__(self, message: str, status_code: int = 502, code: str = "AI_SERVICE_ERROR", details: Any = None):
        super().__init__(message=message, status_code=status_code, code=code, details=details)


class EmbeddingDimensionMismatchException(AIServiceException):
    """Raised when an embedding vector does not match the configured Qdrant collection dimension."""
    def __init__(self, expected_dim: int, actual_dim: int):
        super().__init__(
            message=(
                f"Embedding dimension mismatch: Vector index expected {expected_dim} dimensions, "
                f"but provider returned {actual_dim} dimensions. Re-indexing is required."
            ),
            status_code=409,
            code="EMBEDDING_DIMENSION_MISMATCH",
        )


class DocumentProcessingException(AppException):
    """Raised when document ingestion, parsing, or chunking fails."""
    def __init__(self, message: str, details: Any = None):
        super().__init__(message=message, status_code=422, code="DOCUMENT_PROCESSING_ERROR", details=details)


class ConfigurationException(AppException):
    """Raised when application or provider configuration is invalid or missing."""
    def __init__(self, message: str, details: Any = None):
        super().__init__(message=message, status_code=500, code="CONFIGURATION_ERROR", details=details)

