from pydantic import BaseModel
from typing import Optional

class CopilotQueryRequest(BaseModel):
    query: str
    dataset_id: Optional[str] = None
    model_id: Optional[str] = None

class CopilotQueryResponse(BaseModel):
    response: str
    grounded: bool = True