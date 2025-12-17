from pydantic import BaseModel, Field
from typing import Optional, List, Any, Generic, TypeVar
from datetime import datetime

class DatasetUploadRequest(BaseModel):
    name: str = Field(..., min_length=3, max_length=100)
    description: Optional[str] = Field(None, max_length=500)

class DatasetResponse(BaseModel):
    id: str
    name: str
    description: Optional[str] = None
    rows: int = 0
    columns: int = 0
    file_size: int = 0
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)

class DatasetListResponse(BaseModel):
    datasets: List[DatasetResponse]

# Generic type for pagination
T = TypeVar('T')

class PaginatedResponse(BaseModel, Generic[T]):
    data: List[T]
    total_count: int
    page: int
    page_size: int
    total_pages: int
    has_next: bool = False
    has_prev: bool = False
    
    def __init__(self, **data):
        super().__init__(**data)
        self.has_next = self.page < self.total_pages
        self.has_prev = self.page > 1