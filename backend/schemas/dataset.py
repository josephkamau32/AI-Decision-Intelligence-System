from pydantic import BaseModel
from datetime import datetime
from typing import Optional, Dict, Any

class DatasetUploadRequest(BaseModel):
    name: str
    description: Optional[str] = None

class DatasetInfo(BaseModel):
    id: str
    name: str
    description: Optional[str] = None
    file_path: str
    created_at: datetime
    size: int  # in bytes
    profile: Optional[Dict[str, Any]] = None

class DatasetListResponse(BaseModel):
    datasets: list[DatasetInfo]