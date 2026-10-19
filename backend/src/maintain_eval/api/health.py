from typing import Literal

from fastapi import APIRouter
from pydantic import BaseModel

router = APIRouter()


class HealthStatus(BaseModel):
    status: Literal["ok"] = "ok"


@router.get("/health")
def read_health() -> HealthStatus:
    return HealthStatus()
