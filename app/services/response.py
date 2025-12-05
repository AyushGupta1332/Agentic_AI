import logging
import json
from typing import Dict, Any, List

class AdaptiveResponseGenerator:
    """Generates responses adapted to user preferences and context."""
    
    def __init__(self, groq_client):
        self.groq_client = groq_client
    
    async def generate_adaptive_response(self, 
                                       query: str, 
                                       base_response: str, 
                                       user_context: Dict[str, Any],
                                       proactive_suggestions: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Generate response adapted to user preferences."""
        
        adaptation_prompt = f"""
        You are an adaptive AI assistant. Customize this response based on the user's context and preferences.
        
        Original Query: {query}
        Base Response: {base_response}
        
        User Context: {json.dumps(user_context, indent=2)}
        Proactive Suggestions: {json.dumps(proactive_suggestions, indent=2)}
        
        Guidelines:
        1. Adapt the tone and complexity based on user's communication style
        2. Reference relevant previous conversations when appropriate
        3. Include proactive suggestions naturally if they're relevant
        4. Maintain the core information while personalizing the delivery
        
        Generate an enhanced, personalized response:
        """
        
        try:
            adaptive_response = await self.groq_client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=[{"role": "user", "content": adaptation_prompt}],
                temperature=0.7,
                max_tokens=1200
            )
            
            return {
                "adapted_response": adaptive_response.choices[0].message.content,
                "personalization_applied": True,
                "proactive_suggestions": proactive_suggestions
            }
            
        except Exception as e:
            logging.error(f"Adaptive response generation error: {e}")
            return {
                "adapted_response": base_response,
                "personalization_applied": False,
                "proactive_suggestions": proactive_suggestions
            }
