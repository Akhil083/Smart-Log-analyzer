from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import get_settings
from app.core.scheduler import start_schedular
from app.api.router import api_router


settings = get_settings()

@asynccontextmanager
async def lifespan(app : FastAPI):
    """Manages application Startup and Shutdown events"""

    start_schedular()
    yield


def create_application() -> FastAPI:
    """Application Factory"""
    
    """Using factory function makes app easier to configure and extend across environment"""

    app = FastAPI(
        title = settings.app_name,
        version= settings.app_version,
        debug = settings.debug,
        lifespan=lifespan,
        docs_url="/docs",
        redoc_url= "/redoc",
        openapi_url=f"{settings.api_v1_prefix}/openapi.json"

    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins =[
            "http://127.0.0.1:5500",
            "http://127.0.0.1:3000",
            "http://localhost:5500",
            "http://localhost:3000",
        ], 
        allow_credentials = True,
        allow_methods = ["*"],
        allow_headers=["*"],
    )


    register_routes(app)
    register_api_router(app)

    return app

def register_routes(app : FastAPI) :
    
    @app.get("/",tags = ["Root"])
    async def root() -> dict[str,str]:
        return{
            "message": f"Welcome to {settings.app_name}",
            "version" : settings.app_version,
            "environment" : settings.app_env,
        }
    
    @app.get("/health", tags = ["System"])
    async def health_check() -> JSONResponse:
        return JSONResponse(
            status_code=200,
            content={
                "status": "ok",
                "service" : settings.app_name,
                "version" : settings.app_version,
            },
        )

def register_api_router(app: FastAPI) -> None:
    """
    Mounting API router under the configured API prefix
    """

    app.include_router(api_router, prefix= settings.api_v1_prefix)


app = create_application()

