from __future__ import annotations

from dataclasses import asdict

from fastapi import APIRouter, Depends, Header, Request, Response, status
from sqlalchemy.orm import Session

from myhub.modules.identity.auth_service import AuthService, InvalidCredentials
from myhub.modules.identity.schemas import (
    CeremonyOptionsResponse,
    PasskeyVerificationRequest,
    PasswordEnrollmentRequest,
    PasswordLoginRequest,
    SessionResponse,
)


identity_router = APIRouter(prefix="/api/v1/auth", tags=["authentication"])


def get_session(request: Request):
    factory = request.app.state.session_factory
    with factory() as session:
        yield session


def _service(request: Request, session: Session) -> AuthService:
    return AuthService(session=session, settings=request.app.state.settings)


def _client_key(request: Request) -> str:
    return request.client.host if request.client is not None else "unknown"


def _bearer(authorization: str | None) -> str:
    if not authorization:
        raise InvalidCredentials()
    scheme, separator, token = authorization.partition(" ")
    if separator != " " or scheme.lower() != "bearer" or not token:
        raise InvalidCredentials()
    return token


@identity_router.post(
    "/initial-owner/passkey/options",
    response_model=CeremonyOptionsResponse,
)
def initial_owner_passkey_options(
    request: Request,
    bootstrap_token: str | None = Header(default=None, alias="X-MyHub-Bootstrap-Token"),
    session: Session = Depends(get_session),
) -> CeremonyOptionsResponse:
    result = _service(request, session).initial_owner_passkey_options(
        bootstrap_token=bootstrap_token or "",
    )
    return CeremonyOptionsResponse(**asdict(result))


@identity_router.post(
    "/initial-owner/passkey/verify",
    response_model=SessionResponse,
)
def initial_owner_passkey_verify(
    payload: PasskeyVerificationRequest,
    request: Request,
    bootstrap_token: str | None = Header(default=None, alias="X-MyHub-Bootstrap-Token"),
    session: Session = Depends(get_session),
) -> SessionResponse:
    result = _service(request, session).verify_initial_owner_passkey(
        bootstrap_token=bootstrap_token or "",
        challenge_token=payload.challenge_token,
        credential=payload.credential,
    )
    return SessionResponse(**asdict(result))


@identity_router.post(
    "/initial-owner/password",
    response_model=SessionResponse,
)
def initial_owner_password_enroll(
    payload: PasswordEnrollmentRequest,
    request: Request,
    bootstrap_token: str | None = Header(default=None, alias="X-MyHub-Bootstrap-Token"),
    session: Session = Depends(get_session),
) -> SessionResponse:
    result = _service(request, session).initial_owner_password_enroll(
        bootstrap_token=bootstrap_token or "",
        login_name=payload.login_name,
        password=payload.password,
    )
    return SessionResponse(**asdict(result))


@identity_router.post("/passkey/options", response_model=CeremonyOptionsResponse)
def passkey_authentication_options(
    request: Request,
    session: Session = Depends(get_session),
) -> CeremonyOptionsResponse:
    result = _service(request, session).passkey_authentication_options(
        client_key=_client_key(request),
    )
    return CeremonyOptionsResponse(**asdict(result))


@identity_router.post("/passkey/verify", response_model=SessionResponse)
def passkey_authentication_verify(
    payload: PasskeyVerificationRequest,
    request: Request,
    session: Session = Depends(get_session),
) -> SessionResponse:
    result = _service(request, session).verify_passkey_authentication(
        challenge_token=payload.challenge_token,
        credential=payload.credential,
        client_key=_client_key(request),
    )
    return SessionResponse(**asdict(result))


@identity_router.post("/password/login", response_model=SessionResponse)
def password_login(
    payload: PasswordLoginRequest,
    request: Request,
    session: Session = Depends(get_session),
) -> SessionResponse:
    result = _service(request, session).password_login(
        login_name=payload.login_name,
        password=payload.password,
        client_key=_client_key(request),
    )
    return SessionResponse(**asdict(result))


@identity_router.post("/password/enroll", status_code=status.HTTP_204_NO_CONTENT)
def password_enroll(
    payload: PasswordEnrollmentRequest,
    request: Request,
    authorization: str | None = Header(default=None, alias="Authorization"),
    session: Session = Depends(get_session),
) -> Response:
    _service(request, session).enroll_password_for_session(
        bearer_token=_bearer(authorization),
        login_name=payload.login_name,
        password=payload.password,
    )
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@identity_router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
def logout(
    request: Request,
    authorization: str | None = Header(default=None, alias="Authorization"),
    session: Session = Depends(get_session),
) -> Response:
    _service(request, session).logout(_bearer(authorization))
    return Response(status_code=status.HTTP_204_NO_CONTENT)
