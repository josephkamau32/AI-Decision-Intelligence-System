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
            logger.error(f"Error processing query: {e}")
            error_msg = str(e).lower()
            
            if "api_key" in error_msg or "authentication" in error_msg or "api key" in error_msg:
                return "There was an authentication issue with the AI service. Please verify your Google API key is valid."
            elif "rate" in error_msg or "quota" in error_msg:
                return "The AI service rate limit was exceeded. Please try again in a moment."
            elif "timeout" in error_msg:
                return "The request timed out. Please try again with a simpler question."
            elif "safety" in error_msg or "blocked" in error_msg:
                return "I cannot provide a response to that question. Please try rephrasing your question."
            else:
                return f"I encountered an error processing your question. Please try again or contact support."


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