from pydantic import BaseModel
from typing import Optional


class HealthResponse(BaseModel):
    status: str
    version: str
    timestamp: str
    commit: Optional[str] = None
    environment: Optional[str] = None
