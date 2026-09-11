from __future__ import annotations

from dataclasses import asdict

from fastapi import APIRouter, Depends, Header, Request
from sqlalchemy import select
from sqlalchemy.orm import Session

from myhub.app.schemas import BootstrapRequest, BootstrapResponse, InstanceResponse
from myhub.domain.bootstrap import BootstrapState
from myhub.infrastructure.db.models import FamilyModel, InstanceBootstrapModel
from myhub.modules.administration.bootstrap_repository import BOOTSTRAP_ROW_ID
from myhub.modules.administration.bootstrap_service import BootstrapCommand, BootstrapService

router = APIRouter(prefix="/api/v1")


def get_session(request: Request):
    factory = request.app.state.session_factory
    with factory() as session:
        yield session


@router.get("/instance", response_model=InstanceResponse)
def get_instance(session: Session = Depends(get_session)) -> InstanceResponse:
    record = session.get(InstanceBootstrapModel, BOOTSTRAP_ROW_ID)
    if record is None:
        return InstanceResponse(state=BootstrapState.UNINITIALIZED)

    family_name = None
    if record.family_id:
        family_name = session.scalar(select(FamilyModel.name).where(FamilyModel.id == record.family_id))

    return InstanceResponse(
        state=BootstrapState(record.state),
        instance_id=record.instance_id,
        canonical_url=record.canonical_url,
        family_id=record.family_id,
        family_name=family_name,
        owner_user_id=record.owner_user_id,
        server_public_key=record.server_public_key,
    )


@router.post("/bootstrap", response_model=BootstrapResponse, status_code=201)
def bootstrap_instance(
    payload: BootstrapRequest,
    request: Request,
    bootstrap_token: str | None = Header(default=None, alias="X-MyHub-Bootstrap-Token"),
    session: Session = Depends(get_session),
) -> BootstrapResponse:
    settings = request.app.state.settings
    service = BootstrapService(
        session=session,
        identity_provider=request.app.state.identity_provider,
        expected_token=settings.bootstrap_token.get_secret_value(),
    )
    result = service.bootstrap(
        BootstrapCommand(
            family_name=payload.family_name,
            canonical_url=payload.canonical_url,
            owner_display_name=payload.owner_display_name,
            supplied_token=bootstrap_token or "",
            request_id=request.state.request_id,
        )
    )
    return BootstrapResponse(**asdict(result))
