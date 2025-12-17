from langchain.agents import initialize_agent, AgentType
from langchain.chat_models import ChatOpenAI
from langchain.memory import ConversationBufferMemory
from .tools import tools
from ..utils.config import settings

class AICopilotAgent:
    def __init__(self):
        self.llm = ChatOpenAI(
            temperature=0,
            model="gpt-3.5-turbo",
            openai_api_key=settings.openai_api_key
        )
        self.memory = ConversationBufferMemory(memory_key="chat_history", return_messages=True)
        self.agent = initialize_agent(
            tools=tools,
            llm=self.llm,
            agent=AgentType.CHAT_CONVERSATIONAL_REACT_DESCRIPTION,
            memory=self.memory,
            verbose=True
        )

    def query(self, user_input: str) -> str:
        """Process user query and return response."""
        try:
            response = self.agent.run(user_input)
            return response
        except Exception as e:
            return f"Error processing query: {str(e)}"

    def grounded_response(self, response: str, query: str) -> str:
        """Ensure response is grounded in available data."""
        from .rag import rag_system
        context = rag_system.get_context(query)
        # Check if key elements in response are present in context
        response_lower = response.lower()
        context_lower = context.lower()
        grounded = True
        # Simple heuristic: check for numbers or specific terms
        import re
        numbers = re.findall(r'\d+\.?\d*', response)
        for num in numbers:
            if num not in context:
                grounded = False
                break
        if not grounded:
            response += "\n\nNote: This response may contain information not fully grounded in available data. Please verify."
        return response

copilot_agent = AICopilotAgent()