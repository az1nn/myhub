from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field

from myhub.domain.bootstrap import BootstrapState


class BootstrapRequest(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    family_name: str = Field(min_length=1, max_length=80)
    canonical_url: str = Field(min_length=1, max_length=512)
    owner_display_name: str = Field(min_length=1, max_length=80)


class InstanceResponse(BaseModel):
    state: BootstrapState
    instance_id: str | None = None
    canonical_url: str | None = None
    family_id: str | None = None
    family_name: str | None = None
    owner_user_id: str | None = None
    server_public_key: str | None = None


class BootstrapResponse(BaseModel):
    state: BootstrapState
    instance_id: str
    family_id: str
    owner_user_id: str
    owner_membership_id: str
    canonical_url: str
    server_public_key: str
