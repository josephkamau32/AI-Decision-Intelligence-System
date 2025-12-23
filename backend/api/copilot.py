from fastapi import APIRouter, HTTPException, status, Query
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field
from ..utils.validators import sanitize_input
from ..utils.config import settings
import logging

logger = logging.getLogger(__name__)

router = APIRouter()

class CopilotQuery(BaseModel):
    question: str = Field(..., min_length=1, max_length=2000, description="User's question")
    dataset_id: Optional[str] = Field(None, description="Optional dataset context")
    model_id: Optional[str] = Field(None, description="Optional model context")
    context: Dict[str, Any] = Field(default_factory=dict, description="Additional context")

class CopilotResponse(BaseModel):
    answer: str = Field(..., description="AI-generated response")
    sources: List[str] = Field(default_factory=list, description="Information sources")
    confidence: float = Field(0.0, ge=0.0, le=1.0, description="Response confidence score")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")

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
        
        # Check if Google API key is configured
        if not settings.google_api_key:
            logger.warning("Google API key not configured, returning fallback response")
            return CopilotResponse(
                answer="AI Copilot is not fully configured. Please set the GOOGLE_API_KEY environment variable to enable LLM-powered responses.",
                sources=["System Configuration"],
                confidence=0.0,
                metadata={"error": "missing_api_key"}
            )
        
        # Build context for the agent
        context_str = ""
        if query.dataset_id:
            context_str += f"Working with dataset: {query.dataset_id}. "
        if query.model_id:
            context_str += f"Analyzing model: {query.model_id}. "
        if query.context:
            context_str += f"Additional context: {query.context}. "
        
        # Prepend context to question if available
        full_question = f"{context_str}{question}" if context_str else question
        
        # Import and use the copilot agent
        try:
            from ..copilot.agent import copilot_agent
            
            # Query the agent
            answer = copilot_agent.query(full_question)
            
            # Extract metadata if available
            sources = ["AI Copilot", "System Data"]
            confidence = 0.85
            metadata = {
                "dataset_id": query.dataset_id,
                "model_id": query.model_id,
                "has_context": bool(context_str)
            }
            
            logger.info(f"Successfully generated copilot response (length: {len(answer)})")
            
            return CopilotResponse(
                answer=answer,
                sources=sources,
                confidence=confidence,
                metadata=metadata
            )
            
        except ImportError as e:
            logger.error(f"Failed to import copilot agent: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Copilot agent not properly initialized"
            )
        except Exception as e:
            error_msg = str(e)
            logger.error(f"Copilot agent error: {error_msg}")
            
            # Check for common LLM API errors
            if "api_key" in error_msg.lower() or "authentication" in error_msg.lower():
                return CopilotResponse(
                    answer="There was an authentication issue with the AI service. Please check the API key configuration.",
                    sources=["Error Handler"],
                    confidence=0.0,
                    metadata={"error": "authentication_failed", "details": error_msg}
                )
            elif "rate" in error_msg.lower() or "quota" in error_msg.lower():
                return CopilotResponse(
                    answer="The AI service is currently experiencing high demand. Please try again in a moment.",
                    sources=["Error Handler"],
                    confidence=0.0,
                    metadata={"error": "rate_limit", "details": error_msg}
                )
            elif "timeout" in error_msg.lower():
                return CopilotResponse(
                    answer="The request took too long to process. Please try asking a simpler question or try again later.",
                    sources=["Error Handler"],
                    confidence=0.0,
                    metadata={"error": "timeout", "details": error_msg}
                )
            else:
                # Generic error response
                return CopilotResponse(
                    answer="I encountered an issue processing your question. Please try rephrasing or contact support if the problem persists.",
                    sources=["Error Handler"],
                    confidence=0.0,
                    metadata={"error": "unknown", "details": error_msg}
                )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected copilot error: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to process copilot query"
        )

@router.post("/query", response_model=CopilotResponse)
async def query_copilot(
    query: str = Query(..., min_length=1, max_length=2000),
    dataset_id: Optional[str] = Query(None),
    model_id: Optional[str] = Query(None)
):
    """Alternative endpoint for simple queries."""
    copilot_query = CopilotQuery(
        question=query,
        dataset_id=dataset_id,
        model_id=model_id
    )
    return await ask_copilot(copilot_query)