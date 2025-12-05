import logging
import re
from typing import List, Dict, Any
from app.models import AgentAction, ToolCall
from app.tools.base import BaseTool

class EnhancedQueryAnalysisService:
    """Enhanced service to analyze queries with better classification."""
    def __init__(self, tools: List[BaseTool], groq_client):
        self.tools = {tool.name: tool for tool in tools}
        self.tool_schemas = self._generate_tool_schemas()
        self.groq_client = groq_client

    def _generate_tool_schemas(self) -> List[Dict[str, Any]]:
        schemas = []
        for tool in self.tools.values():
            if tool.name == "social_media_search":
                schema = {
                    "type": "function",
                    "function": {
                        "name": tool.name,
                        "description": tool.description,
                        "parameters": {
                            "type": "object",
                            "properties": {
                                "query": {"type": "string", "description": "The search query"},
                                "platform": {"type": "string", "description": "The social media platform (instagram, twitter, tiktok, etc.)"}
                            },
                            "required": ["query"]
                        }
                    }
                }
            elif tool.name == "get_stock_info":
                schema = {
                    "type": "function",
                    "function": {
                        "name": tool.name,
                        "description": tool.description,
                        "parameters": {
                            "type": "object",
                            "properties": {
                                "ticker": {"type": "string", "description": "Stock ticker symbol (e.g., 'AAPL')"}
                            },
                            "required": ["ticker"]
                        }
                    }
                }
            else:
                schema = {
                    "type": "function",
                    "function": {
                        "name": tool.name,
                        "description": tool.description,
                        "parameters": {
                            "type": "object",
                            "properties": {
                                "query": {"type": "string", "description": "The search query"}
                            },
                            "required": ["query"]
                        }
                    }
                }
            schemas.append(schema)
        return schemas

    async def get_plan(self, query: str, conversation_history: List[Dict[str, str]]) -> AgentAction:
        logging.info("Generating an enhanced plan for the query...")
        
        # Enhanced classification prompt
        classification_prompt = """
        Analyze the user's message and classify it into one of these categories:

        1. CASUAL - Simple greetings, small talk, acknowledgments
        Examples: "hi", "hello", "how are you", "thanks", "goodbye", "ok"

        2. SOCIAL_MEDIA - Questions about social media platforms, statistics, trends
        Examples: "most liked image on Instagram", "trending on TikTok", "Twitter followers"

        3. FINANCIAL - Stock prices, market data, financial information
        Examples: "Apple stock price", "TSLA earnings", "market cap of Google"

        4. NEWS - Current events, recent news, breaking news
        Examples: "latest news about", "what happened with", "recent developments"

        5. GENERAL_WEB - General information, facts, explanations
        Examples: "what is", "how does", "explain", "tell me about"

        6. MEMORY - Questions about the conversation history, past interactions, or user preferences
        Examples: "what did I ask first?", "summarize our chat", "what was the last thing you said?", "do you remember my name?"

        Respond with only the category name: CASUAL, SOCIAL_MEDIA, FINANCIAL, NEWS, GENERAL_WEB, or MEMORY
        """
        
        try:
            classification_response = await self.groq_client.chat.completions.create(
                model="llama-3.1-8b-instant",
                messages=[
                    {"role": "system", "content": classification_prompt},
                    {"role": "user", "content": query}
                ],
                temperature=0.0,
                max_tokens=20
            )
            
            classification = classification_response.choices[0].message.content.strip().upper()
            
            if "CASUAL" in classification:
                return AgentAction(tool_calls=[], log="Detected casual conversation - no tools needed")
            
            if "MEMORY" in classification:
                return AgentAction(tool_calls=[], log="Detected memory query - using conversation context")
            
            # Determine appropriate tools based on classification
            tool_calls = []
            
            if "SOCIAL_MEDIA" in classification:
                # Extract platform if mentioned
                platform = "instagram"  # default
                query_lower = query.lower()
                if "twitter" in query_lower or "x.com" in query_lower:
                    platform = "twitter"
                elif "tiktok" in query_lower:
                    platform = "tiktok"
                elif "facebook" in query_lower:
                    platform = "facebook"
                elif "youtube" in query_lower:
                    platform = "youtube"
                
                tool_calls.append(ToolCall(
                    name="social_media_search",
                    parameters={"query": query, "platform": platform}
                ))
                
                # Also do a general web search as backup
                tool_calls.append(ToolCall(
                    name="web_search",
                    parameters={"query": query}
                ))
            
            elif "FINANCIAL" in classification:
                # Try to extract ticker symbol using LLM
                ticker = None
                try:
                    extraction_prompt = f"""
                    Extract the stock ticker symbol from this query: "{query}"
                    Return ONLY the ticker symbol (e.g., AAPL, TSLA). 
                    If no specific company/ticker is mentioned, return "NONE".
                    """
                    completion = await self.groq_client.chat.completions.create(
                        model="llama-3.1-8b-instant",
                        messages=[{"role": "user", "content": extraction_prompt}],
                        temperature=0.0,
                        max_tokens=10
                    )
                    extracted = completion.choices[0].message.content.strip().upper()
                    match = re.search(r'\b[A-Z]{1,5}\b', extracted)
                    if match and "NONE" not in extracted:
                        ticker = match.group()
                except Exception as e:
                    logging.error(f"Ticker extraction failed: {e}")

                if ticker:
                    tool_calls.append(ToolCall(
                        name="get_stock_info",
                        parameters={"ticker": ticker}
                    ))
                else:
                    # If no clear ticker, do web search for financial info
                    tool_calls.append(ToolCall(
                        name="web_search",
                        parameters={"query": query}
                    ))
            
            elif "NEWS" in classification:
                tool_calls.append(ToolCall(
                    name="news_search",
                    parameters={"query": query}
                ))
                
                # Also do web search as backup
                tool_calls.append(ToolCall(
                    name="web_search",
                    parameters={"query": query}
                ))
            
            else:  # GENERAL_WEB
                tool_calls.append(ToolCall(
                    name="web_search",
                    parameters={"query": query}
                ))
            
            if tool_calls:
                return AgentAction(
                    tool_calls=tool_calls,
                    log=f"Classified as {classification}, using tools: {[tc.name for tc in tool_calls]}"
                )
            else:
                return AgentAction(tool_calls=[], log="No suitable tools found for this query")
                
        except Exception as e:
            logging.error(f"Error in enhanced query analysis: {e}")
            # Fallback to web search
            return AgentAction(
                tool_calls=[ToolCall(name="web_search", parameters={"query": query})],
                log=f"Error during classification, defaulting to web search: {e}"
            )
