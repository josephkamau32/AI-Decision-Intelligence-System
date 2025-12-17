from fastapi import APIRouter, HTTPException, status, Query
from typing import List, Dict, Any
from pydantic import BaseModel
from ..utils.validators import sanitize_input
import logging

logger = logging.getLogger(__name__)

router = APIRouter()

class CopilotQuery(BaseModel):
    question: str
    dataset_id: str = None
    model_id: str = None
    context: Dict[str, Any] = {}

class CopilotResponse(BaseModel):
    answer: str
    sources: List[str] = []
    confidence: float = 0.0

@router.post("/ask", response_model=CopilotResponse)
async def ask_copilot(query: CopilotQuery):
    """Ask AI Copilot a question with optional context."""
    logger.info(f"Copilot query: {query.question[:100]}")
    
    try:
        # Sanitize input
        question = sanitize_input(query.question, max_length=2000)
        
        if not question:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Question cannot be empty"
            )
        
        # TODO: Integrate with actual LLM service (OpenAI, etc.)
        # For now, return a mock response
        answer = f"I understand you're asking about: '{question}'. "
        answer += "This is a mock response. In production, this would be powered by an LLM like GPT-4. "
        
        if query.dataset_id:
            answer += f"I can see you're working with dataset {query.dataset_id}. "
        if query.model_id:
            answer += f"For model {query.model_id}, "
        
        answer += "I would provide detailed insights, recommendations, and explanations based on your data and models."
        
        return CopilotResponse(
            answer=answer,
            sources=["AI Decision Intelligence System"],
            confidence=0.85
        )
    
    except Exception as e:
        logger.error(f"Copilot error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to process copilot query"
        )

@router.post("/query", response_model=CopilotResponse)
async def query_copilot(
    query: str = Query(..., min_length=1, max_length=2000),
    dataset_id: str = Query(None),
    model_id: str = Query(None)
):
    """Alternative endpoint for simple queries."""
    copilot_query = CopilotQuery(
        question=query,
        dataset_id=dataset_id,
        model_id=model_id
    )
    return await ask_copilot(copilot_query)