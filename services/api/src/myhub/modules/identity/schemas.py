from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


class CeremonyOptionsResponse(BaseModel):
    challenge_token: str
    public_key: dict[str, Any]


class PasskeyVerificationRequest(BaseModel):
    challenge_token: str = Field(min_length=20, max_length=200)
    credential: dict[str, Any]


class PasswordEnrollmentRequest(BaseModel):
    login_name: str = Field(min_length=1, max_length=160)
    password: str = Field(min_length=1, max_length=4096)


class PasswordLoginRequest(BaseModel):
    login_name: str = Field(min_length=1, max_length=160)
    password: str = Field(min_length=1, max_length=4096)


class SessionResponse(BaseModel):
    user_id: str
    session_id: str
    bearer_token: str
    expires_at: datetime
