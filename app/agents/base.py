from typing import Dict, Any
from groq import AsyncGroq
from config import GROQ_API_KEY

class BaseSpecializedAgent:
    """Base class for specialized agents."""
    def __init__(self, name: str, specialization: str):
        self.name = name
        self.specialization = specialization
        self.groq_client = AsyncGroq(api_key=GROQ_API_KEY)

    async def can_handle(self, query: str) -> bool:
        """Determine if this agent can handle the query."""
        raise NotImplementedError

    async def process(self, query: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Process the query with specialized knowledge."""
        raise NotImplementedError
