from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, SystemMessage
from ..utils.config import settings
import logging

logger = logging.getLogger(__name__)

class AICopilotAgent:
    def __init__(self):
        """Initialize the AI Copilot with ChatOpenAI."""
        try:
            self.llm = ChatOpenAI(
                temperature=0.7,
                model="gpt-3.5-turbo",
                openai_api_key=settings.openai_api_key or "dummy-key"  # Prevent initialization error
            )
            logger.info("AI Copilot initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize copilot: {e}")
            self.llm = None

    def query(self, user_input: str) -> str:
        """
        Process user query and return response.
        
        Args:
            user_input: The user's question
            
        Returns:
            AI-generated response string
        """
        try:
            if not self.llm:
                return "AI Copilot is not properly initialized. Please check the configuration."
            
            if not settings.openai_api_key:
                return "AI Copilot requires an OpenAI API key to be configured. Please set OPENAI_API_KEY in your environment."
            
            # Create messages for the chat
            messages = [
                SystemMessage(content="You are a helpful AI assistant for a data analytics platform. You help users understand their datasets, models, and analytics results. Provide clear, concise, and accurate responses."),
                HumanMessage(content=user_input)
            ]
            
            # Get response from OpenAI
            response = self.llm.invoke(messages)
            return response.content
            
        except Exception as e:
            logger.error(f"Error processing query: {e}")
            error_msg = str(e).lower()
            
            if "api_key" in error_msg or "authentication" in error_msg:
                return "There was an authentication issue with the AI service. Please verify your OpenAI API key is valid."
            elif "rate" in error_msg or "quota" in error_msg:
                return "The AI service rate limit was exceeded. Please try again in a moment."
            elif "timeout" in error_msg:
                return "The request timed out. Please try again with a simpler question."
            else:
                return f"I encountered an error processing your question: {str(e)}"

# Create singleton instance
try:
    copilot_agent = AICopilotAgent()
    logger.info("Copilot agent singleton created")
except Exception as e:
    logger.error(f"Failed to create copilot agent: {e}")
    copilot_agent = None