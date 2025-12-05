import logging
from typing import Dict, Any
from app.agents.base import BaseSpecializedAgent

class CreativeAgent(BaseSpecializedAgent):
    """Agent specialized in creative tasks and content generation."""
    def __init__(self):
        super().__init__("CreativeAgent", "creative_content")

    async def can_handle(self, query: str) -> bool:
        creative_keywords = ['write', 'create', 'generate', 'compose', 'draft', 'brainstorm', 'ideas', 'creative', 'story', 'poem', 'article']
        return any(keyword in query.lower() for keyword in creative_keywords)

    async def process(self, query: str, context: Dict[str, Any]) -> Dict[str, Any]:
        logging.info(f"🎨 CreativeAgent processing: {query}")
        
        creative_prompt = f"""
        You are a creative AI assistant. The user has requested: {query}
        
        Provide creative, original content that directly fulfills their request.
        Be imaginative, engaging, and helpful. Structure your response appropriately for the content type requested.
        """
        
        try:
            creative_response = await self.groq_client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=[{"role": "user", "content": creative_prompt}],
                temperature=0.8,
                max_tokens=800
            )
            
            return {
                "agent": self.name,
                "creative_content": creative_response.choices[0].message.content,
                "content_type": self._detect_content_type(query)
            }
        except Exception as e:
            logging.error(f"Creative generation error: {e}")
            return {
                "agent": self.name,
                "creative_content": "I'd be happy to help with creative tasks, but I'm experiencing some technical difficulties right now.",
                "content_type": "error"
            }

    def _detect_content_type(self, query: str) -> str:
        if any(word in query.lower() for word in ['story', 'tale', 'narrative']):
            return "story"
        elif any(word in query.lower() for word in ['poem', 'poetry', 'verse']):
            return "poetry"
        elif any(word in query.lower() for word in ['article', 'blog', 'post']):
            return "article"
        elif any(word in query.lower() for word in ['list', 'ideas', 'brainstorm']):
            return "list"
        else:
            return "general_creative"
