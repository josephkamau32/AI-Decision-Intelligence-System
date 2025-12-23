"""AI Copilot Agent using Google Generative AI directly (no langchain)"""
import google.generativeai as genai
from ..utils.config import settings
import logging

logger = logging.getLogger(__name__)

class AICopilotAgent:
    def __init__(self):
        """Initialize the AI Copilot with Google Gemini."""
        try:
            # Check if API key is available
            if not settings.google_api_key:
                logger.warning("Google API key is not set")
                self.model = None
                return
            
            # Configure Google Generative AI
            genai.configure(api_key=settings.google_api_key)
            
            # Create the model
            self.model = genai.GenerativeModel('gemini-1.5-flash')
            
            logger.info("✓ AI Copilot initialized successfully with Google Gemini")
        except Exception as e:
            logger.error(f"Failed to initialize copilot: {e}")
            self.model = None

    def query(self, user_input: str) -> str:
        """
        Process user query and return response.
        
        Args:
            user_input: The user's question
            
        Returns:
            AI-generated response string
        """
        try:
            if not self.model:
                if not settings.google_api_key:
                    return "AI Copilot requires a Google API key to be configured. Please set GOOGLE_API_KEY in your environment."
                return "AI Copilot is not properly initialized. Please check the configuration."
            
            # Create system context + user question
            prompt = f"""You are a helpful AI assistant for a data analytics platform called Decisera. 
You help users understand their datasets, models, and analytics results. 
Provide clear, concise, and accurate responses.

User question: {user_input}"""
            
            # Get response from Gemini
            response = self.model.generate_content(prompt)
            return response.text
            
        except Exception as e:
            # Log the full error for debugging
            logger.error(f"Copilot error: {type(e).__name__}: {str(e)}")
            
            error_msg = str(e).lower()
            error_type = type(e).__name__
            
            # Check for specific Google API errors
            if "resourceexhausted" in error_type.lower():
                logger.warning("Google API quota exceeded")
                return "The AI service quota has been exceeded. Please try again later or check your API quota at https://console.cloud.google.com/apis/api/generativelanguage.googleapis.com/quotas"
            elif "api_key" in error_msg or "authentication" in error_msg or "api key" in error_msg or "unauthenticated" in error_type.lower():
                return "There was an authentication issue with the AI service. Please verify your Google API key is valid."
            elif "permissiondenied" in error_type.lower() or "permission" in error_msg:
                return "Permission denied. Please check that your API key has access to the Gemini API."
            elif "timeout" in error_msg:
                return "The request timed out. Please try again with a simpler question."
            elif "safety" in error_msg or "blocked" in error_msg:
                return "I cannot provide a response to that question due to content safety policies. Please try rephrasing your question."
            else:
                # Return a generic error with the actual error type for debugging
                logger.error(f"Unhandled error type: {error_type}")
                return f"I encountered an error: {error_type}. Please try again or contact support if this persists."


# Lazy singleton initialization - ensures settings are loaded first
_copilot_agent_instance = None

def get_copilot_agent() -> AICopilotAgent:
    """Get or create the copilot agent singleton (lazy initialization)"""
    global _copilot_agent_instance
    
    if _copilot_agent_instance is None:
        try:
            logger.info("Initializing AI Copilot agent (lazy load)...")
            _copilot_agent_instance = AICopilotAgent()
            logger.info("✓ Copilot agent initialized successfully")
        except Exception as e:
            logger.error(f"Failed to create copilot agent: {e}")
            # Create a blank instance as fallback
            _copilot_agent_instance = AICopilotAgent()
    
    return _copilot_agent_instance


# Create a proxy class that uses lazy loading
class CopilotAgentProxy:
    """Proxy class that lazily initializes the copilot agent"""
    
    def query(self, user_input: str) -> str:
        """Forward query to the lazily-initialized agent"""
        return get_copilot_agent().query(user_input)


# Export the proxy as copilot_agent for backward compatibility
copilot_agent = CopilotAgentProxy()