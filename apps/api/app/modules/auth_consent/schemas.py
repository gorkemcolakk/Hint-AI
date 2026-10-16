import uuid
from datetime import datetime
from typing import Literal

from pydantic import BaseModel, EmailStr, Field, field_validator

ALLOWED_PURPOSES = ("service", "analytics", "llm_processing", "photo_processing")
SolutionPolicy = Literal[
    "never", "after_attempts_with_notice", "guardian_only", "similar_example_only"
]
PrivacyLevel = Literal["summary_only", "full_transcript"]


class RegisterRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)
    role: Literal["guardian", "teacher"]
    full_name: str | None = None


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class ChildTokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


class RefreshRequest(BaseModel):
    refresh_token: str


class LogoutRequest(BaseModel):
    refresh_token: str


class ChildCreateRequest(BaseModel):
    nickname: str = Field(min_length=1, max_length=100)
    birth_year: int = Field(ge=1900, le=2100)
    grade: int = Field(ge=1, le=12)
    purposes: list[str] = Field(default_factory=lambda: ["service"])

    @field_validator("purposes")
    @classmethod
    def validate_purposes(cls, value: list[str]) -> list[str]:
        for purpose in value:
            if purpose not in ALLOWED_PURPOSES:
                raise ValueError(f"Geçersiz amaç: {purpose}")
        return value


class ChildPatchRequest(BaseModel):
    nickname: str | None = Field(default=None, min_length=1, max_length=100)
    daily_new_problem_limit: int | None = Field(default=None, ge=0, le=100)
    solution_policy: SolutionPolicy | None = None
    privacy_level: PrivacyLevel | None = None


class ConsentRequest(BaseModel):
    purposes: list[str] = Field(min_length=1)
    grant: bool

    @field_validator("purposes")
    @classmethod
    def validate_purposes(cls, value: list[str]) -> list[str]:
        for purpose in value:
            if purpose not in ALLOWED_PURPOSES:
                raise ValueError(f"Geçersiz amaç: {purpose}")
        return value


class PairingCodeResponse(BaseModel):
    code: str
    expires_at: datetime


class ChildPairRequest(BaseModel):
    child_id: uuid.UUID
    code: str


class ChildProfileResponse(BaseModel):
    id: uuid.UUID
    nickname: str
    birth_year: int
    grade: int
    age_band: str
    daily_new_problem_limit: int
    solution_policy: str
    privacy_level: str
