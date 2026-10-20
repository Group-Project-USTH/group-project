from fastapi import FastAPI

from maintainability_agent.api.routers import health


def create_app() -> FastAPI:
    app = FastAPI(title="maintainability-agent")
    app.include_router(health.router)
    return app
