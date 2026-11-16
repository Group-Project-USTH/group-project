from typing import Literal

from fastapi import APIRouter
from pydantic import BaseModel

router = APIRouter(prefix="/health", tags=["health"])


class HealthStatus(BaseModel):
    status: Literal["ok"] = "ok"


@router.get("")
def read_health() -> HealthStatus:
    return HealthStatus()
