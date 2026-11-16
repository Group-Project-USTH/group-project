from fastapi import FastAPI

from maintainability_lens.api.routers import health


def create_app() -> FastAPI:
    app = FastAPI(title="maintainability-lens")
    app.include_router(health.router)
    return app
