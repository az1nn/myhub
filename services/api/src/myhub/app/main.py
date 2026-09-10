from __future__ import annotations

from fastapi import FastAPI
from sqlalchemy import Engine

from myhub.app.errors import bootstrap_error_handler, internal_error_handler
from myhub.app.middleware import RequestIdMiddleware
from myhub.app.routes import router
from myhub.infrastructure.db.session import build_engine, build_session_factory
from myhub.infrastructure.identity import Ed25519InstanceIdentityProvider
from myhub.modules.administration.bootstrap_service import BootstrapError
from myhub.modules.administration.config import Settings, get_settings


def create_app(*, settings: Settings | None = None, engine: Engine | None = None) -> FastAPI:
    settings = settings or get_settings()
    engine = engine or build_engine(settings.database_url)

    app = FastAPI(title="MyHub API", version="0.1.0")
    app.state.settings = settings
    app.state.engine = engine
    app.state.session_factory = build_session_factory(engine)
    app.state.identity_provider = Ed25519InstanceIdentityProvider()

    app.add_middleware(RequestIdMiddleware)
    app.add_exception_handler(BootstrapError, bootstrap_error_handler)
    app.add_exception_handler(Exception, internal_error_handler)
    app.include_router(router)
    return app
