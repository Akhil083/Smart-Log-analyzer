from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

from app.api.router import api_router
from app.core.config import get_settings
from app.core.scheduler import start_schedular

settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manages application Startup and Shutdown events"""

    start_schedular()
    yield


def create_application() -> FastAPI:
    """Application Factory"""

    """Using factory function makes app easier to configure and extend across environment"""

    app = FastAPI(
        title=settings.app_name,
        version=settings.app_version,
        debug=settings.debug,
        lifespan=lifespan,
        docs_url="/docs",
        redoc_url="/redoc",
        openapi_url=f"{settings.api_v1_prefix}/openapi.json",
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=[
            "http://127.0.0.1:5500",
            "http://127.0.0.1:3000",
            "http://localhost:5500",
            "http://localhost:3000",
        ],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    register_routes(app)
    register_api_router(app)

    app.mount(
        "/static",
        StaticFiles(directory="frontend"),
        name="static",
    )

    return app


def register_routes(app: FastAPI):

    @app.get("/", include_in_schema=False)
    async def home():
        return FileResponse("frontend/pages/index.html")

    @app.get("/logs", include_in_schema=False)
    async def logs_page():
        return FileResponse("frontend/pages/logs.html")

    @app.get("/analytics", include_in_schema=False)
    async def analytics_page():
        return FileResponse("frontend/pages/analytics.html")

    @app.get("/alerts", include_in_schema=False)
    async def alerts_page():
        return FileResponse("frontend/pages/alerts.html")

    @app.get("/settings", include_in_schema=False)
    async def settings_page():
        return FileResponse("frontend/pages/settings.html")

    @app.get("/health", tags=["System"])
    async def health_check() -> JSONResponse:
        return JSONResponse(
            status_code=200,
            content={
                "status": "ok",
                "service": settings.app_name,
                "version": settings.app_version,
            },
        )


def register_api_router(app: FastAPI) -> None:
    """
    Mounting API router under the configured API prefix
    """

    app.include_router(api_router, prefix=settings.api_v1_prefix)


app = create_application()
