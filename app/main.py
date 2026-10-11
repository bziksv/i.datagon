import os

from fastapi import Depends, FastAPI
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession
from starlette.exceptions import HTTPException as StarletteHTTPException
from starlette.requests import Request

from app import __version__
from app.db import get_db, ping_session

PUBLIC_PATHS = frozenset({"/health", "/ready"})


def error_payload(code: str, message: str) -> dict[str, str]:
    return {"code": code, "message": message}


def create_app() -> FastAPI:
    prod = os.environ.get("APP_ENV", "dev") == "prod"
    app = FastAPI(
        title="i.datagon",
        version=__version__,
        docs_url=None if prod else "/docs",
        redoc_url=None if prod else "/redoc",
        openapi_url=None if prod else "/openapi.json",
    )
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["https://i.datagon.ru", "http://i.datagon.ru"],
        allow_origin_regex=r"http://(localhost|127\.0\.0\.1)(:\d+)?",
        allow_credentials=True,
        allow_methods=["GET", "POST"],
        allow_headers=["Authorization", "Content-Type", "X-App-Token"],
    )

    @app.middleware("http")
    async def require_app_token(request: Request, call_next):
        if request.method == "OPTIONS" or request.url.path in PUBLIC_PATHS:
            return await call_next(request)
        expected = os.environ.get("APP_AUTH_TOKEN", "")
        got = request.headers.get("X-App-Token", "")
        if not expected or got != expected:
            return JSONResponse(
                status_code=401, content=error_payload("401", "unauthorized")
            )
        return await call_next(request)

    @app.exception_handler(StarletteHTTPException)
    async def http_error(
        _request: Request, exc: StarletteHTTPException
    ) -> JSONResponse:
        message = exc.detail if isinstance(exc.detail, str) else str(exc.detail)
        return JSONResponse(
            status_code=exc.status_code,
            content=error_payload(str(exc.status_code), message),
        )

    @app.exception_handler(RequestValidationError)
    async def validation_error(
        _request: Request, exc: RequestValidationError
    ) -> JSONResponse:
        return JSONResponse(
            status_code=422,
            content=error_payload("422", str(exc.errors())),
        )

    @app.get("/health")
    def health() -> dict[str, str]:
        return {"status": "ok"}

    @app.get("/version")
    def version() -> dict[str, str]:
        return {"version": __version__}

    @app.get("/ready")
    async def ready(session: AsyncSession = Depends(get_db)) -> dict[str, str]:
        await ping_session(session)
        return {"status": "ok"}

    return app
