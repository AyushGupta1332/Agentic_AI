import logging
import json
from datetime import datetime
from typing import List, Dict, Any, Optional
from app.tools.base import BaseTool

class DynamicToolDiscovery:
    """Discovers and creates new tools dynamically based on user needs."""
    
    def __init__(self, groq_client):
        self.groq_client = groq_client
        self.discovered_tools = {}
        self.tool_templates = {}
        self.performance_metrics = {}
    
    async def analyze_tool_needs(self, query: str, available_tools: List[str]) -> Dict[str, Any]:
        """Analyze if new tools are needed for the query."""
        analysis_prompt = f"""
        Analyze this user query to determine if new tools or capabilities are needed:
        
        Query: "{query}"
        Available Tools: {available_tools}
        
        Determine:
        1. Can existing tools handle this query effectively? (yes/no)
        2. What specific new tool would be most helpful?
        3. What would this new tool do?
        4. Priority level (low/medium/high)
        
        Respond in JSON format:
        {{
            "needs_new_tool": boolean,
            "suggested_tool_name": "string",
            "tool_description": "string",
            "tool_capabilities": ["capability1", "capability2"],
            "priority": "low/medium/high",
            "reasoning": "explanation"
        }}
        """
        
        try:
            analysis_response = await self.groq_client.chat.completions.create(
                model="llama-3.1-8b-instant",
                messages=[{"role": "user", "content": analysis_prompt}],
                temperature=0.3,
                max_tokens=400
            )
            
            response_text = analysis_response.choices[0].message.content
            # Extract JSON from response
            import re
            json_match = re.search(r'\{.*\}', response_text, re.DOTALL)
            if json_match:
                return json.loads(json_match.group())
            
        except Exception as e:
            logging.error(f"Tool analysis error: {e}")
        
        return {"needs_new_tool": False, "reasoning": "Analysis failed"}
    
    async def create_dynamic_tool(self, tool_spec: Dict[str, Any]) -> Optional[str]:
        """Create a new tool dynamically based on specifications."""
        tool_name = tool_spec.get("suggested_tool_name", "").replace(" ", "_").lower()
        
        if not tool_name:
            return None
        
        tool_code_prompt = f"""
        Create a Python class for a new tool based on these specifications:
        
        Tool Name: {tool_spec.get("suggested_tool_name")}
        Description: {tool_spec.get("tool_description")}
        Capabilities: {tool_spec.get("tool_capabilities", [])}
        
        Create a class that inherits from BaseTool with:
        1. Proper __init__ method
        2. async execute method that takes **kwargs
        3. Error handling
        4. Logging
        5. Returns structured data
        
        Keep it simple but functional. Focus on the core capability.
        Only return the Python class code, no explanations.
        """
        
        try:
            code_response = await self.groq_client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=[{"role": "user", "content": tool_code_prompt}],
                temperature=0.2,
                max_tokens=1000
            )
            
            tool_code = code_response.choices[0].message.content
            
            # Store the generated tool
            self.discovered_tools[tool_name] = {
                "name": tool_name,
                "code": tool_code,
                "spec": tool_spec,
                "created": datetime.utcnow().isoformat(),
                "usage_count": 0
            }
            
            logging.info(f"✅ Created dynamic tool: {tool_name}")
            return tool_name
            
        except Exception as e:
            logging.error(f"Dynamic tool creation error: {e}")
            return None
    
    def get_tool_suggestions(self, context: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Get suggestions for useful tools based on context."""
        suggestions = []
        
        # Analyze user patterns for tool suggestions
        user_topics = context.get("user_preferences", {}).get("preferred_topics", {})
        
        if "technology" in user_topics:
            suggestions.append({
                "name": "GitHub Repository Analyzer",
                "description": "Analyzes GitHub repositories for insights",
                "priority": "medium"
            })
        
        if "business" in user_topics:
            suggestions.append({
                "name": "Market Trend Analyzer",
                "description": "Advanced market trend analysis tool",
                "priority": "high"
            })
        
        if "creative" in user_topics:
            suggestions.append({
                "name": "Content Strategy Generator",
                "description": "Generates content strategies and ideas",
                "priority": "medium"
            })
        
        return suggestions
