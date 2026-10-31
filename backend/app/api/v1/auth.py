from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.db.session import get_db_session
from app.models.user import User
from app.schemas.auth import (
    SetPasswordRequest,
    SignupResponse,
    TokenResponse,
    UserLoginRequest,
    UserRegisterRequest,
    UserResponse,
    UserSignupRequest,
)
from app.services.auth_service import AuthService

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post("/signup", response_model=SignupResponse, status_code=status.HTTP_200_OK)
async def signup(
    data: UserSignupRequest,
    session: AsyncSession = Depends(get_db_session),
) -> SignupResponse:
    """
    Step 1 of signup: Enter email only. An activation email is dispatched containing
    a secure link to set your password. Supports public Mailinator inboxes.
    """
    auth_service = AuthService(session)
    return await auth_service.signup_request(data)


@router.post("/set-password", response_model=TokenResponse)
async def set_password(
    data: SetPasswordRequest,
    session: AsyncSession = Depends(get_db_session),
) -> TokenResponse:
    """
    Step 2 of signup: Set password from activation link and receive JWT access token.
    """
    auth_service = AuthService(session)
    return await auth_service.set_password(data)


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register(
    data: UserRegisterRequest,
    session: AsyncSession = Depends(get_db_session),
) -> UserResponse:
    """Register a new user account."""
    auth_service = AuthService(session)
    return await auth_service.register(data)


@router.post("/login", response_model=TokenResponse)
async def login(
    data: UserLoginRequest,
    session: AsyncSession = Depends(get_db_session),
) -> TokenResponse:
    """Authenticate credentials and generate JWT access token."""
    auth_service = AuthService(session)
    return await auth_service.login(data)


@router.get("/me", response_model=UserResponse)
async def get_me(
    current_user: User = Depends(get_current_user),
) -> UserResponse:
    """Retrieve details for currently authenticated user."""
    return UserResponse.model_validate(current_user)


@router.post("/logout")
async def logout(
    current_user: User = Depends(get_current_user),
) -> dict[str, str]:
    """Client-side token disposal endpoint."""
    return {"message": "Successfully logged out."}

