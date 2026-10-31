import uuid
from datetime import datetime
from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator


class UserSignupRequest(BaseModel):
    email: EmailStr = Field(..., description="Email address to receive the password setup link")

    @field_validator("email")
    @classmethod
    def normalize_email(cls, v: str) -> str:
        return v.strip().lower()


class SignupResponse(BaseModel):
    message: str
    email: str
    mailinator_url: str | None = None


class SetPasswordRequest(BaseModel):
    token: str = Field(..., description="Signed activation token received in the email")
    password: str = Field(..., min_length=8, max_length=128, description="New secure password")


class UserRegisterRequest(BaseModel):
    email: EmailStr = Field(..., description="User's unique email address")
    password: str = Field(..., min_length=8, max_length=128, description="User's secure password")

    @field_validator("email")
    @classmethod
    def normalize_email(cls, v: str) -> str:
        return v.strip().lower()


class UserLoginRequest(BaseModel):
    email: EmailStr
    password: str = Field(..., max_length=128)

    @field_validator("email")
    @classmethod
    def normalize_email(cls, v: str) -> str:
        return v.strip().lower()


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in_seconds: int


class UserResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    email: str
    is_active: bool
    is_superuser: bool = False
    role: str = "user"
    created_at: datetime
    updated_at: datetime
