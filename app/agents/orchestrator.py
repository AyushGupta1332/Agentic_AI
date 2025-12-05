import logging
import json
from datetime import datetime
from typing import Dict, Any, List, Optional
from groq import AsyncGroq
from config import GROQ_API_KEY
from app.agents.base import BaseSpecializedAgent
from app.agents.research import ResearchAgent
from app.agents.analysis import AnalysisAgent
from app.agents.creative import CreativeAgent

class AgentOrchestrator:
    """Orchestrates multiple specialized agents."""
    def __init__(self):
        self.agents = [
            ResearchAgent(),
            AnalysisAgent(),
            CreativeAgent()
        ]
        self.groq_client = AsyncGroq(api_key=GROQ_API_KEY)

    async def select_best_agent(self, query: str) -> Optional[BaseSpecializedAgent]:
        """Select the most appropriate agent for the query."""
        suitable_agents = []
        
        for agent in self.agents:
            if await agent.can_handle(query):
                suitable_agents.append(agent)
        
        if not suitable_agents:
            return None
        
        # If multiple agents can handle it, use the first one for now
        # Later we can add more sophisticated selection logic
        return suitable_agents[0]

    async def process_with_specialist(self, query: str, conversation_history: List[Dict[str, str]]) -> Dict[str, Any]:
        """Process query with the most appropriate specialist agent."""
        selected_agent = await self.select_best_agent(query)
        
        if not selected_agent:
            return {"error": "No suitable specialist agent found"}
        
        context = {
            "conversation_history": conversation_history,
            "timestamp": datetime.utcnow().isoformat()
        }
        
        specialist_result = await selected_agent.process(query, context)
        
        # Generate final response using specialist results
        synthesis_prompt = f"""
        A specialist agent ({selected_agent.name}) has processed this query: "{query}"
        
        Agent Results: {json.dumps(specialist_result, indent=2)}
        
        Synthesize this information into a comprehensive, user-friendly response.
        Be informative, well-structured, and directly address the user's query.
        """
        
        try:
            final_response = await self.groq_client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=[{"role": "user", "content": synthesis_prompt}],
                temperature=0.7,
                max_tokens=1000
            )
            
            return {
                "content": final_response.choices[0].message.content,
                "specialist_agent": selected_agent.name,
                "specialist_results": specialist_result,
                "processing_method": "multi_agent"
            }
        except Exception as e:
            logging.error(f"Multi-agent synthesis error: {e}")
            return {"error": f"Specialist processing failed: {str(e)}"}
