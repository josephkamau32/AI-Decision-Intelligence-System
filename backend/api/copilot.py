from fastapi import APIRouter, HTTPException
from ..schemas.copilot import CopilotQueryRequest, CopilotQueryResponse
from ..copilot.agent import copilot_agent
from ..copilot.rag import rag_system

router = APIRouter()

@router.post("/query", response_model=CopilotQueryResponse)
async def query_copilot(request: CopilotQueryRequest):
    """Query the AI Copilot for insights."""
    try:
        # Index relevant data if provided
        if request.dataset_id:
            rag_system.index_dataset(request.dataset_id)
        if request.model_id:
            rag_system.index_model_insights(request.model_id)

        response = copilot_agent.query(request.query)
        grounded_response = copilot_agent.grounded_response(response, request.query)
        return CopilotQueryResponse(response=grounded_response)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Copilot query failed: {str(e)}")