import logging
from typing import Dict, Any
from app.agents.base import BaseSpecializedAgent
from app.tools.search import EnhancedWebSearchTool, EnhancedNewsSearchTool

class ResearchAgent(BaseSpecializedAgent):
    """Agent specialized in research and information gathering."""
    def __init__(self):
        super().__init__("ResearchAgent", "information_research")
        self.web_tool = EnhancedWebSearchTool()
        self.news_tool = EnhancedNewsSearchTool()

    async def can_handle(self, query: str) -> bool:
        research_keywords = ['research', 'find information', 'tell me about', 'what is', 'explain', 'how does', 'latest news', 'recent developments']
        return any(keyword in query.lower() for keyword in research_keywords)

    async def process(self, query: str, context: Dict[str, Any]) -> Dict[str, Any]:
        logging.info(f"🔬 ResearchAgent processing: {query}")
        
        # Determine best research strategy
        if 'news' in query.lower() or 'recent' in query.lower():
            primary_results = await self.news_tool.execute(query, 5)
            secondary_results = await self.web_tool.execute(query, 3)
        else:
            primary_results = await self.web_tool.execute(query, 8)
            secondary_results = []

        return {
            "agent": self.name,
            "primary_results": primary_results,
            "secondary_results": secondary_results,
            "research_strategy": "news_focused" if 'news' in query.lower() else "web_focused"
        }
