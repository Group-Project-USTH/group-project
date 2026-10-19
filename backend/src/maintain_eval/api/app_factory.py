from fastapi import FastAPI

from maintain_eval.api import health


def create_app() -> FastAPI:
    app = FastAPI(title="maintain-eval")
    app.include_router(health.router)
    return app
