import uuid
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import AuthenticationException, EntityAlreadyExistsException
from app.core.security import (
    create_access_token,
    create_set_password_token,
    decode_set_password_token,
    get_password_hash,
    verify_password,
)
from app.models.user import User
from app.repositories.user_repository import UserRepository
from app.schemas.auth import (
    SetPasswordRequest,
    SignupResponse,
    TokenResponse,
    UserLoginRequest,
    UserRegisterRequest,
    UserResponse,
    UserSignupRequest,
)
from app.services.email_service import EmailService


class AuthService:
    def __init__(self, session: AsyncSession):
        self.session = session
        self.user_repo = UserRepository(session)

    async def signup_request(self, data: UserSignupRequest) -> SignupResponse:
        """Step 1 of signup: register email, create pending account, and send activation link."""
        user = await self.user_repo.get_by_email(data.email)
        if user and user.is_active:
            raise EntityAlreadyExistsException(f"An active account with email '{data.email}' already exists.")

        if not user:
            # Create user in pending activation state
            user = User(
                email=data.email,
                password_hash="!PENDING_SET_PASSWORD!",
                is_active=False,
            )
            user = await self.user_repo.create(user)
            await self.session.commit()

        # Generate signed activation token
        token = create_set_password_token(subject=str(user.id), email=user.email)

        # Dispatch email
        sent, _, mailinator_url = EmailService.send_set_password_email(user.email, token)

        return SignupResponse(
            message="Signup initiated. Please check your email to set your password and activate your account.",
            email=user.email,
            mailinator_url=mailinator_url,
        )

    async def set_password(self, data: SetPasswordRequest) -> TokenResponse:
        """Step 2 of signup: validate token from email, set password, and activate account."""
        payload = decode_set_password_token(data.token)
        user_id_str = payload.get("sub")
        user_id = uuid.UUID(user_id_str)

        user = await self.user_repo.get_by_id(user_id)
        if not user:
            raise AuthenticationException("User account not found.")

        # Set verified password and activate account
        user.password_hash = get_password_hash(data.password)
        user.is_active = True
        await self.session.commit()

        # Issue immediate access token so the user is logged in
        token = create_access_token(subject=str(user.id))
        from app.core.config import settings

        return TokenResponse(
            access_token=token,
            token_type="bearer",
            expires_in_seconds=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        )

    async def register(self, data: UserRegisterRequest) -> UserResponse:
        existing = await self.user_repo.get_by_email(data.email)
        if existing:
            raise EntityAlreadyExistsException(f"User with email '{data.email}' already exists.")

        hashed_password = get_password_hash(data.password)
        new_user = User(
            email=data.email,
            password_hash=hashed_password,
            is_active=True,
        )
        created_user = await self.user_repo.create(new_user)
        await self.session.commit()
        await self.session.refresh(created_user)
        return UserResponse.model_validate(created_user)

    async def login(self, data: UserLoginRequest) -> TokenResponse:
        user = await self.user_repo.get_by_email(data.email)
        if not user or not verify_password(data.password, user.password_hash):
            raise AuthenticationException("Invalid email or password.")

        if not user.is_active:
            raise AuthenticationException("Account is inactive.")

        token = create_access_token(subject=str(user.id))
        from app.core.config import settings

        return TokenResponse(
            access_token=token,
            token_type="bearer",
            expires_in_seconds=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        )

