# main.py

# This script contains the entire backend logic for the agentic AI with Flask UI.

# --- IMPORTS ---

import os
import asyncio
import json
from datetime import datetime
import logging
from typing import List, Dict, Any, Optional, Union
from flask import Flask, render_template, request, jsonify
from flask_socketio import SocketIO, emit, disconnect
from flask_cors import CORS
import threading
from pydantic import BaseModel, Field
import httpx
from duckduckgo_search import DDGS
import yfinance as yf
from groq import Groq, AsyncGroq
import chromadb
from chromadb.utils import embedding_functions
import re

# --- CONFIGURATION ---

# Hardcoded GROQ API Key
# GROQ_API_KEY = "your groq_api_key_here"  # Replace with your actual Groq API key

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# --- INITIALIZE FLASK APP ---

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your-secret-key-change-this-in-production'

# Add CORS support
CORS(app, resources={
    r"/*": {
        "origins": "*",
        "methods": ["GET", "POST"],
        "allow_headers": ["Content-Type"]
    }
})

# Initialize SocketIO with CORS and logging enabled
socketio = SocketIO(app,
                   cors_allowed_origins="*",
                   async_mode='threading',
                   logger=True,
                   engineio_logger=True)

# --- INITIALIZE SERVICES ---

# Check if the API key is provided before initializing
if not GROQ_API_KEY:
    raise ValueError("GROQ_API_KEY is not set. Please hardcode your API key.")

groq_client = AsyncGroq(api_key=GROQ_API_KEY)

# ChromaDB Client for Memory
try:
    chroma_client = chromadb.PersistentClient(path="./chroma_db")
    embedding_function = embedding_functions.SentenceTransformerEmbeddingFunction(model_name="all-MiniLM-L6-v2")
    memory_collection = chroma_client.get_or_create_collection(
        name="agentic_memory",
        embedding_function=embedding_function,
        metadata={"hnsw:space": "cosine"}
    )
    print("✅ ChromaDB initialized successfully")
except Exception as e:
    print(f"⚠️ ChromaDB initialization failed: {e}")
    chroma_client = None
    memory_collection = None

# --- Pydantic Schemas for Data Validation ---

class ToolCall(BaseModel):
    name: str
    parameters: Dict[str, Any]

class AgentAction(BaseModel):
    tool_calls: List[ToolCall]
    log: str

# --- ENHANCED TOOLS ---

class BaseTool:
    """Base class for all tools."""
    def __init__(self, name: str, description: str):
        self.name = name
        self.description = description

    async def execute(self, **kwargs) -> Any:
        raise NotImplementedError("Each tool must implement the execute method.")

class EnhancedWebSearchTool(BaseTool):
    """Enhanced tool for performing web searches with multiple strategies."""
    def __init__(self):
        super().__init__(
            name="web_search",
            description="Searches the web for information on a given query with multiple search strategies and language filtering."
        )

    def _filter_non_english_results(self, results: List[Dict]) -> List[Dict]:
        """Filter out non-English results based on title and content analysis."""
        filtered_results = []
        for result in results:
            title = result.get('title', '')
            snippet = result.get('snippet', result.get('body', ''))
            
            # Basic language detection - check if result contains mostly English characters
            combined_text = f"{title} {snippet}"
            english_chars = sum(1 for char in combined_text if char.isascii() and char.isalpha())
            total_chars = sum(1 for char in combined_text if char.isalpha())
            
            # If more than 70% of alphabetic characters are ASCII, consider it English
            if total_chars > 0 and (english_chars / total_chars) >= 0.7:
                filtered_results.append(result)
        
        return filtered_results

    def _enhance_query(self, query: str) -> List[str]:
        """Generate multiple enhanced queries for better search results."""
        enhanced_queries = [query]
        
        # Add specific search operators and variations
        if "most" in query.lower() and ("liked" in query.lower() or "popular" in query.lower()):
            enhanced_queries.extend([
                f"{query} site:instagram.com",
                f"{query} official statistics",
                f"{query} 2024 2025",
                f"{query} record breaking",
                f'"{query}" -site:baidu.com -site:zhihu.com'
            ])
        elif "stock" in query.lower() or "price" in query.lower():
            enhanced_queries.extend([
                f"{query} today current",
                f"{query} real time",
                f"{query} market data"
            ])
        elif "news" in query.lower():
            enhanced_queries.extend([
                f"{query} latest breaking",
                f"{query} today 2025",
                f"{query} recent updates"
            ])
        else:
            enhanced_queries.extend([
                f"{query} 2025",
                f"{query} latest information",
                f'"{query}" official'
            ])
        
        return enhanced_queries[:3]  # Limit to 3 queries

    async def execute(self, query: str, num_results: int = 8) -> List[Dict[str, str]]:
        logging.info(f"Executing enhanced web search for query: {query}")
        all_results = []
        
        try:
            enhanced_queries = self._enhance_query(query)
            
            for search_query in enhanced_queries:
                try:
                    with DDGS() as ddgs:
                        # Search with region preference for English results
                        results = [r for r in ddgs.text(
                            search_query, 
                            max_results=num_results,
                            region='us-en',  # Prefer US English results
                            safesearch='moderate'
                        )]
                        
                        for result in results:
                            formatted_result = {
                                "title": result.get('title', ''),
                                "snippet": result.get('body', ''),
                                "url": result.get('href', ''),
                                "query_used": search_query
                            }
                            all_results.append(formatted_result)
                
                except Exception as e:
                    logging.warning(f"Error with query '{search_query}': {e}")
                    continue
            
            # Filter non-English results
            filtered_results = self._filter_non_english_results(all_results)
            
            # Remove duplicates based on URL
            seen_urls = set()
            unique_results = []
            for result in filtered_results:
                url = result.get('url', '')
                if url not in seen_urls:
                    seen_urls.add(url)
                    unique_results.append(result)
            
            # Sort by relevance (prioritize exact matches and official sources)
            def relevance_score(result):
                score = 0
                title = result.get('title', '').lower()
                snippet = result.get('snippet', '').lower()
                url = result.get('url', '').lower()
                
                # Prioritize official sources
                if any(domain in url for domain in ['instagram.com', 'facebook.com', 'twitter.com', 'linkedin.com']):
                    score += 10
                
                # Prioritize recent content
                if any(year in title + snippet for year in ['2024', '2025']):
                    score += 5
                
                # Prioritize exact query matches
                query_words = query.lower().split()
                title_words = title.split()
                if all(word in title_words for word in query_words):
                    score += 8
                
                return score
            
            unique_results.sort(key=relevance_score, reverse=True)
            
            return unique_results[:num_results] if unique_results else [
                {"error": "No relevant English results found for this query"}
            ]
            
        except Exception as e:
            logging.error(f"Error during enhanced web search: {e}")
            return [{"error": str(e)}]

class EnhancedNewsSearchTool(BaseTool):
    """Enhanced tool for searching recent news with better filtering."""
    def __init__(self):
        super().__init__(
            name="news_search",
            description="Searches for recent news articles with enhanced filtering and relevance."
        )

    async def execute(self, query: str, num_results: int = 5) -> List[Dict[str, str]]:
        logging.info(f"Executing enhanced news search for query: {query}")
        try:
            with DDGS() as ddgs:
                # Multiple search attempts with different time ranges
                results = []
                
                # Try recent news first
                try:
                    recent_results = [r for r in ddgs.news(
                        query, 
                        max_results=num_results * 2,
                        region='us-en',
                        safesearch='moderate'
                    )]
                    results.extend(recent_results)
                except:
                    pass
                
                # If not enough results, try broader search
                if len(results) < num_results:
                    try:
                        broader_results = [r for r in ddgs.news(
                            f"{query} news", 
                            max_results=num_results,
                            region='us-en'
                        )]
                        results.extend(broader_results)
                    except:
                        pass
                
                formatted_results = []
                seen_urls = set()
                
                for result in results:
                    url = result.get('url', '')
                    if url not in seen_urls:
                        seen_urls.add(url)
                        formatted_results.append({
                            "title": result.get('title', ''),
                            "source": result.get('source', ''),
                            "date": result.get('date', ''),
                            "url": url,
                            "snippet": result.get('body', '')[:200] + "..." if result.get('body') else ""
                        })
                
                return formatted_results[:num_results] if formatted_results else [
                    {"error": "No recent news found for this query"}
                ]
                
        except Exception as e:
            logging.error(f"Error during enhanced news search: {e}")
            return [{"error": str(e)}]

class SocialMediaSearchTool(BaseTool):
    """Tool specifically for social media related queries."""
    def __init__(self):
        super().__init__(
            name="social_media_search",
            description="Searches for social media statistics, trends, and information from platforms like Instagram, Twitter, TikTok, etc."
        )

    async def execute(self, query: str, platform: str = "instagram") -> List[Dict[str, str]]:
        logging.info(f"Executing social media search for: {query} on {platform}")
        try:
            # Construct platform-specific search queries
            search_queries = [
                f"{query} site:{platform}.com",
                f"{query} {platform} official statistics",
                f"{query} {platform} records data",
                f'"{query}" {platform} -site:baidu.com -site:zhihu.com'
            ]
            
            all_results = []
            
            with DDGS() as ddgs:
                for search_query in search_queries:
                    try:
                        results = [r for r in ddgs.text(
                            search_query,
                            max_results=3,
                            region='us-en'
                        )]
                        
                        for result in results:
                            all_results.append({
                                "title": result.get('title', ''),
                                "snippet": result.get('body', ''),
                                "url": result.get('href', ''),
                                "platform": platform,
                                "search_query": search_query
                            })
                    except:
                        continue
            
            # Remove duplicates and filter for relevance
            seen_urls = set()
            unique_results = []
            
            for result in all_results:
                url = result.get('url', '')
                if url not in seen_urls and platform in result.get('url', '').lower():
                    seen_urls.add(url)
                    unique_results.append(result)
            
            return unique_results[:5] if unique_results else [
                {"error": f"No {platform} specific results found for this query"}
            ]
            
        except Exception as e:
            logging.error(f"Error during social media search: {e}")
            return [{"error": str(e)}]

class FinancialTool(BaseTool):
    """Enhanced financial tool with better error handling."""
    def __init__(self):
        super().__init__(
            name="get_stock_info",
            description="Fetches comprehensive financial information for stock tickers with enhanced data validation."
        )

    async def execute(self, ticker: str) -> Dict[str, Any]:
        logging.info(f"Executing enhanced financial data fetch for ticker: {ticker}")
        try:
            # Clean and validate ticker
            ticker = ticker.upper().strip()
            
            stock = yf.Ticker(ticker)
            info = stock.info
            
            # Check if we got valid data
            if not info or 'symbol' not in info:
                return {"error": f"No valid data found for ticker '{ticker}'. Please check the symbol."}
            
            # Get additional data
            hist = stock.history(period="5d")
            
            result = {
                "symbol": info.get("symbol"),
                "longName": info.get("longName"),
                "currentPrice": info.get("currentPrice"),
                "previousClose": info.get("previousClose"),
                "open": info.get("open"),
                "dayHigh": info.get("dayHigh"),
                "dayLow": info.get("dayLow"),
                "volume": info.get("volume"),
                "marketCap": info.get("marketCap"),
                "fiftyTwoWeekHigh": info.get("fiftyTwoWeekHigh"),
                "fiftyTwoWeekLow": info.get("fiftyTwoWeekLow"),
                "forwardPE": info.get("forwardPE"),
                "sector": info.get("sector"),
                "industry": info.get("industry"),
                "currency": info.get("currency", "USD")
            }
            
            # Add price change calculation
            if result["currentPrice"] and result["previousClose"]:
                price_change = result["currentPrice"] - result["previousClose"]
                price_change_percent = (price_change / result["previousClose"]) * 100
                result["priceChange"] = round(price_change, 2)
                result["priceChangePercent"] = round(price_change_percent, 2)
            
            return result
            
        except Exception as e:
            logging.error(f"Error fetching financial data for {ticker}: {e}")
            return {"error": f"Could not fetch data for ticker '{ticker}'. Error: {str(e)}"}


# --- MULTI-AGENT SYSTEM ---

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

class AnalysisAgent(BaseSpecializedAgent):
    """Agent specialized in data analysis and insights."""
    def __init__(self):
        super().__init__("AnalysisAgent", "data_analysis")
        self.financial_tool = FinancialTool()

    async def can_handle(self, query: str) -> bool:
        analysis_keywords = ['analyze', 'compare', 'statistics', 'data', 'trends', 'insights', 'stock', 'price', 'financial', 'market']
        return any(keyword in query.lower() for keyword in analysis_keywords)

    async def process(self, query: str, context: Dict[str, Any]) -> Dict[str, Any]:
        logging.info(f"📊 AnalysisAgent processing: {query}")
        
        results = {}
        
        # Check if it's financial analysis
        import re
        ticker_match = re.search(r'\b[A-Z]{1,5}\b', query.upper())
        if ticker_match or any(keyword in query.lower() for keyword in ['stock', 'price', 'financial']):
            if ticker_match:
                financial_data = await self.financial_tool.execute(ticker_match.group())
                results["financial_analysis"] = financial_data
        
        # Generate analytical insights
        analysis_prompt = f"""
        Analyze the following query for key analytical insights:
        Query: {query}
        
        Provide structured analysis focusing on:
        1. Key metrics to consider
        2. Comparative analysis approach
        3. Trend indicators
        
        Keep response concise and analytical.
        """
        
        try:
            analysis_response = await self.groq_client.chat.completions.create(
                model="llama-3.1-8b-instant",
                messages=[{"role": "user", "content": analysis_prompt}],
                temperature=0.3,
                max_tokens=300
            )
            results["analytical_insights"] = analysis_response.choices[0].message.content
        except Exception as e:
            logging.error(f"Analysis generation error: {e}")
            results["analytical_insights"] = "Analysis temporarily unavailable."

        return {
            "agent": self.name,
            "analysis_results": results,
            "analysis_type": "financial" if ticker_match else "general"
        }

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



# --- ENHANCED SERVICES ---

class EnhancedQueryAnalysisService:
    """Enhanced service to analyze queries with better classification."""
    def __init__(self, tools: List[BaseTool]):
        self.tools = {tool.name: tool for tool in tools}
        self.tool_schemas = self._generate_tool_schemas()

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

        Respond with only the category name: CASUAL, SOCIAL_MEDIA, FINANCIAL, NEWS, or GENERAL_WEB
        """
        
        try:
            classification_response = await groq_client.chat.completions.create(
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
                # Try to extract ticker symbol
                import re
                ticker_match = re.search(r'\b[A-Z]{1,5}\b', query.upper())
                if ticker_match:
                    tool_calls.append(ToolCall(
                        name="get_stock_info",
                        parameters={"ticker": ticker_match.group()}
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

# Continue with the rest of the services and classes (same as before but use EnhancedQueryAnalysisService)

class InformationProcessingService:
    """Service to synthesize information from tool outputs into a coherent response."""
    
    async def synthesize_response(self, query: str, tool_outputs: Dict[str, Any], conversation_history: List[Dict[str, str]], is_casual: bool = False) -> Dict[str, Any]:
        logging.info("Synthesizing final response...")
        
        if is_casual or not tool_outputs:
            # Handle casual conversation (same as before)
            casual_prompt = """
            You are a friendly and helpful AI assistant. The user sent a casual message that doesn't require any information gathering.
            Respond naturally and conversationally, keeping it brief, warm, and friendly.
            
            Examples:
            - If they say "Hi there" or "Hello" → "Hello! How can I help you today?"
            - If they say "How are you?" → "I'm doing great, thank you for asking! How can I assist you?"
            - If they say "Thanks" or "Thank you" → "You're welcome! Is there anything else I can help you with?"
            - If they say "Good morning" → "Good morning! What can I do for you today?"
            - If they say "What's up?" → "Not much, just here to help! What would you like to know?"
            - If they introduce themselves → "Nice to meet you! I'm here to help with any questions you have."
            
            Keep responses friendly, concise (1-2 sentences), and always offer to help.
            """
            
            messages = [
                {"role": "system", "content": casual_prompt},
                *conversation_history[-3:],
                {"role": "user", "content": query}
            ]
            
            try:
                chat_completion = await groq_client.chat.completions.create(
                    model="llama-3.1-8b-instant",
                    messages=messages,
                    temperature=0.7,
                    max_tokens=150
                )
                
                content = chat_completion.choices[0].message.content
                
                return {
                    "content": content,
                    "confidence_score": 95,
                    "sources": []
                }
                
            except Exception as e:
                logging.error(f"Error in casual response generation: {e}")
                return {
                    "content": "Hello! How can I assist you today?",
                    "confidence_score": 90,
                    "sources": []
                }
        
        # Check if we have any errors in tool outputs
        has_errors = any(
            isinstance(output, dict) and "error" in output 
            or (isinstance(output, list) and len(output) > 0 and isinstance(output[0], dict) and "error" in output[0])
            for output in tool_outputs.values()
        )
        
        if has_errors:
            # Enhanced error handling
            system_prompt = """
            The search tools couldn't find good results for this query. Provide a helpful response that:
            1. Acknowledges the limitation
            2. Suggests alternative approaches
            3. Offers to help with related questions
            4. Provides any general knowledge you might have (but clearly indicate it's general knowledge)
            
            Be honest about limitations while still being helpful.
            """
        else:
            # Enhanced success response
            system_prompt = """
            You are an AI assistant that synthesizes information from various sources to provide a comprehensive, well-structured, and coherent answer to the user's query.
            
            IMPORTANT FORMATTING RULES:
            - DO NOT include any URLs or links in your response text
            - Focus only on providing the factual information clearly
            - Use clean, readable formatting with proper paragraphs
            - DO NOT mention sources by URL in your response
            - Keep the response well-structured and easy to read
            - Use markdown formatting for better readability (bold, headers, lists when appropriate)
            - If you mention specific information, do NOT include the source URLs inline
            - If multiple tools provided similar information, synthesize it coherently
            - If there are conflicting results, mention the discrepancy
            
            Your job is to provide clean, informative content. The sources will be handled separately.
            """

        # Clean the tool outputs
        cleaned_outputs = self._clean_tool_outputs_for_prompt(tool_outputs)

        prompt = f"""
        User Query: {query}
        Information from Tools: {json.dumps(cleaned_outputs, indent=2)}
        
        Based on the above information, provide a clear and comprehensive answer. 
        Do not include any URLs or source references in your response.
        """

        messages = [
            {"role": "system", "content": system_prompt},
            *conversation_history,
            {"role": "user", "content": prompt}
        ]

        try:
            chat_completion = await groq_client.chat.completions.create(
                model="llama-3.1-8b-instant",
                messages=messages,
                temperature=0.7,
            )

            content = chat_completion.choices[0].message.content

            # Adjust confidence based on whether we had errors
            base_confidence = 60 if has_errors else 85
            
            # Get confidence score
            confidence_score_prompt = f"Based on the following response and whether the search tools found good results (errors present: {has_errors}), what is your confidence score (0-100) in its accuracy and completeness?\n\nResponse: {content}\n\nConfidence Score:"
            try:
                score_completion = await groq_client.chat.completions.create(
                    model="llama-3.1-8b-instant",
                    messages=[{"role": "user", "content": confidence_score_prompt}],
                    temperature=0.0,
                )
                score_text = score_completion.choices[0].message.content
                confidence = int(''.join(filter(str.isdigit, score_text))) if any(char.isdigit() for char in score_text) else base_confidence
            except:
                confidence = base_confidence

            return {
                "content": content,
                "confidence_score": confidence,
                "sources": self._extract_sources(tool_outputs)
            }

        except Exception as e:
            logging.error(f"Error in response synthesis: {e}")
            return {
                "content": "I apologize, but I encountered an error while processing your request. Please try rephrasing your question or ask something else.",
                "confidence_score": 20,
                "sources": []
            }

    def _clean_tool_outputs_for_prompt(self, tool_outputs: Dict[str, Any]) -> Dict[str, Any]:
        """Clean tool outputs by removing URLs to prevent them from appearing in the response."""
        cleaned_outputs = {}
        
        for tool_name, output in tool_outputs.items():
            if isinstance(output, list):
                cleaned_list = []
                for item in output:
                    if isinstance(item, dict):
                        cleaned_item = {k: v for k, v in item.items() if k not in ['url', 'query_used', 'search_query']}
                        cleaned_list.append(cleaned_item)
                    else:
                        cleaned_list.append(item)
                cleaned_outputs[tool_name] = cleaned_list
            elif isinstance(output, dict):
                cleaned_outputs[tool_name] = {k: v for k, v in output.items() if k not in ['url', 'query_used', 'search_query']}
            else:
                cleaned_outputs[tool_name] = output
        
        return cleaned_outputs

    def _extract_sources(self, tool_outputs: Dict[str, Any]) -> List[Dict[str, str]]:
        """Extract sources with better formatting and numbering."""
        sources = []
        source_counter = 1
        
        for tool_name, output in tool_outputs.items():
            if isinstance(output, list):
                for item in output:
                    if isinstance(item, dict) and 'url' in item and 'error' not in item:
                        title = item.get("title") or item.get("source") or f"Source {source_counter}"
                        # Clean up title - remove excessive whitespace and truncate if too long
                        title = re.sub(r'\s+', ' ', title.strip())
                        if len(title) > 100:
                            title = title[:97] + "..."
                        
                        sources.append({
                            "id": source_counter,
                            "title": title,
                            "url": item.get("url"),
                            "type": self._determine_source_type(tool_name, item.get("url", "")),
                            "platform": item.get("platform", "")
                        })
                        source_counter += 1
            elif isinstance(output, dict) and 'symbol' in output:
                sources.append({
                    "id": source_counter,
                    "title": f"Yahoo Finance - {output['symbol']}",
                    "url": f"https://finance.yahoo.com/quote/{output['symbol']}",
                    "type": "financial",
                    "platform": "yahoo_finance"
                })
                source_counter += 1
        
        return sources
    
    def _determine_source_type(self, tool_name: str, url: str) -> str:
        """Determine the type of source based on tool and URL."""
        if "financial" in tool_name or "stock" in tool_name:
            return "financial"
        elif "news" in tool_name:
            return "news"
        elif "social_media" in tool_name:
            return "social"
        elif any(domain in url.lower() for domain in ['instagram.com', 'twitter.com', 'facebook.com', 'tiktok.com']):
            return "social"
        else:
            return "web"

# Keep the same MemoryService class as before

class MemoryService:
    """Service for managing the agent's memory using ChromaDB."""
    
    def add_to_memory(self, user_id: str, query: str, response: str):
        if not memory_collection:
            return
        logging.info("Adding interaction to memory.")
        try:
            document = f"User query: {query}\nAI response: {response}"
            doc_id = f"{user_id}-{datetime.utcnow().isoformat()}"
            memory_collection.add(
                documents=[document],
                metadatas=[{"user_id": user_id, "timestamp": datetime.utcnow().timestamp()}],
                ids=[doc_id]
            )
        except Exception as e:
            logging.error(f"Error adding to memory: {e}")

    def search_memory(self, user_id: str, query: str, n_results: int = 3) -> List[str]:
        if not memory_collection:
            return []
        logging.info("Searching memory for relevant context.")
        try:
            results = memory_collection.query(
                query_texts=[query],
                n_results=n_results,
                where={"user_id": user_id}
            )
            return results.get('documents', [[]])[0]
        except Exception as e:
            logging.error(f"Error searching memory: {e}")
            return []

# --- ENHANCED CORE AGENT ---

# --- ENHANCED CORE AGENT ---

class EnhancedAgent:
    """Enhanced main agent with multi-agent orchestration."""
    
    def __init__(self):
        self.tools = [
            EnhancedWebSearchTool(),
            EnhancedNewsSearchTool(),
            SocialMediaSearchTool(),
            FinancialTool()
        ]
        self.analysis_service = EnhancedQueryAnalysisService(self.tools)
        self.processing_service = InformationProcessingService()
        self.memory_service = MemoryService()
        self.tool_mapping = {tool.name: tool for tool in self.tools}
        
        # NEW: Add multi-agent orchestrator
        self.agent_orchestrator = AgentOrchestrator()

    async def run(self, user_id: str, query: str, conversation_history: List[Dict[str, str]]):
        start_time = datetime.utcnow()
        
        # Send initial status update
        socketio.emit('status_update', {"message": "🔍 Analyzing your query..."}, room=user_id)
        
        # NEW: Try multi-agent processing first
        socketio.emit('status_update', {"message": "🤖 Selecting specialist agent..."}, room=user_id)
        
        try:
            multi_agent_result = await self.agent_orchestrator.process_with_specialist(query, conversation_history)
            
            if "error" not in multi_agent_result:
                # Multi-agent processing successful
                socketio.emit('status_update', {"message": f"✅ Processed by {multi_agent_result.get('specialist_agent', 'specialist')}"}, room=user_id)
                
                end_time = datetime.utcnow()
                processing_time = (end_time - start_time).total_seconds()
                
                response_payload = {
                    "response": multi_agent_result.get("content"),
                    "confidence": 90,  # High confidence for specialist agents
                    "sources": self._extract_sources_from_specialist(multi_agent_result.get("specialist_results", {})),
                    "processing_time": round(processing_time, 2),
                    "method": f"Multi-Agent: {multi_agent_result.get('specialist_agent', 'Unknown')}",
                    "tools_used": 1,
                    "sources_found": len(self._extract_sources_from_specialist(multi_agent_result.get("specialist_results", {})))
                }
                
                # Store in memory
                if memory_collection:
                    asyncio.create_task(self._add_to_memory_async(user_id, query, multi_agent_result.get("content", "")))
                
                socketio.emit('final_response', response_payload, room=user_id)
                return response_payload
                
        except Exception as e:
            logging.warning(f"Multi-agent processing failed, falling back to standard processing: {e}")
            socketio.emit('status_update', {"message": "🔄 Switching to standard processing..."}, room=user_id)
        
        # FALLBACK: Original processing method
        # 1. Enhanced Planning
        plan = await self.analysis_service.get_plan(query, conversation_history)
        socketio.emit('status_update', {"message": f"📋 {plan.log}"}, room=user_id)

        # 2. Enhanced Tool Execution
        tool_outputs = {}
        is_casual = len(plan.tool_calls) == 0 and "casual conversation" in plan.log.lower()
        
        if plan.tool_calls:
            socketio.emit('status_update', {"message": f"🔧 Executing {len(plan.tool_calls)} tool(s)..."}, room=user_id)
            
            # Execute tools with better error handling
            for i, tool_call in enumerate(plan.tool_calls):
                if tool_call.name in self.tool_mapping:
                    try:
                        socketio.emit('status_update',
                                    {"message": f"⚙️ Running {tool_call.name} ({i+1}/{len(plan.tool_calls)})..."},
                                    room=user_id)
                        
                        tool = self.tool_mapping[tool_call.name]
                        result = await tool.execute(**tool_call.parameters)
                        tool_outputs[tool_call.name] = result
                        
                        # Provide feedback on tool results
                        if isinstance(result, list) and len(result) > 0:
                            socketio.emit('status_update',
                                        {"message": f"✅ {tool_call.name} found {len(result)} results"},
                                        room=user_id)
                        elif isinstance(result, dict) and "error" not in result:
                            socketio.emit('status_update',
                                        {"message": f"✅ {tool_call.name} completed successfully"},
                                        room=user_id)
                        else:
                            socketio.emit('status_update',
                                        {"message": f"⚠️ {tool_call.name} had limited results"},
                                        room=user_id)
                            
                    except Exception as e:
                        logging.error(f"Error executing tool {tool_call.name}: {e}")
                        tool_outputs[tool_call.name] = {"error": str(e)}
                        socketio.emit('status_update',
                                    {"message": f"❌ {tool_call.name} encountered an error"},
                                    room=user_id)
                else:
                    logging.warning(f"Tool '{tool_call.name}' not found.")

        # 3. Enhanced Response Synthesis
        socketio.emit('status_update',
                     {"message": "🧠 Generating your response..." if is_casual else "🔬 Synthesizing information..."},
                     room=user_id)
        
        final_response_data = await self.processing_service.synthesize_response(
            query, tool_outputs, conversation_history, is_casual
        )

        # 4. Memory Storage
        if memory_collection:
            asyncio.create_task(self._add_to_memory_async(user_id, query, final_response_data.get("content", "")))

        # 5. Send enhanced final response
        end_time = datetime.utcnow()
        processing_time = (end_time - start_time).total_seconds()
        
        response_payload = {
            "response": final_response_data.get("content"),
            "confidence": final_response_data.get("confidence_score"),
            "sources": final_response_data.get("sources"),
            "processing_time": round(processing_time, 2),
            "method": "Casual Chat" if is_casual else (
                "Direct Answer" if not plan.tool_calls else
                f"Enhanced Search: {[tc.name for tc in plan.tool_calls]}"
            ),
            "tools_used": len(plan.tool_calls),
            "sources_found": len(final_response_data.get("sources", []))
        }

        socketio.emit('final_response', response_payload, room=user_id)
        return response_payload

    async def _add_to_memory_async(self, user_id: str, query: str, response: str):
        self.memory_service.add_to_memory(user_id, query, response)

    def _extract_sources_from_specialist(self, specialist_results: Dict[str, Any]) -> List[Dict[str, str]]:
        """Extract sources from specialist agent results."""
        sources = []
        source_counter = 1
        
        # Extract from research agent results
        if "primary_results" in specialist_results:
            for item in specialist_results["primary_results"]:
                if isinstance(item, dict) and 'url' in item and 'error' not in item:
                    title = item.get("title") or item.get("source") or f"Source {source_counter}"
                    # Clean up title
                    import re
                    title = re.sub(r'\s+', ' ', title.strip())
                    if len(title) > 100:
                        title = title[:97] + "..."
                    
                    sources.append({
                        "id": source_counter,
                        "title": title,
                        "url": item.get("url"),
                        "type": "research",
                        "platform": ""
                    })
                    source_counter += 1
        
        # Extract from secondary results
        if "secondary_results" in specialist_results:
            for item in specialist_results["secondary_results"]:
                if isinstance(item, dict) and 'url' in item and 'error' not in item:
                    title = item.get("title") or item.get("source") or f"Source {source_counter}"
                    import re
                    title = re.sub(r'\s+', ' ', title.strip())
                    if len(title) > 100:
                        title = title[:97] + "..."
                    
                    sources.append({
                        "id": source_counter,
                        "title": title,
                        "url": item.get("url"),
                        "type": "research_secondary",
                        "platform": ""
                    })
                    source_counter += 1
        
        # Extract from analysis agent results
        if "analysis_results" in specialist_results and "financial_analysis" in specialist_results["analysis_results"]:
            financial_data = specialist_results["analysis_results"]["financial_analysis"]
            if "symbol" in financial_data and "error" not in financial_data:
                sources.append({
                    "id": source_counter,
                    "title": f"Yahoo Finance - {financial_data['symbol']}",
                    "url": f"https://finance.yahoo.com/quote/{financial_data['symbol']}",
                    "type": "financial",
                    "platform": "yahoo_finance"
                })
                source_counter += 1
        
        return sources


# Keep the same ConnectionManager and Flask routes, but use EnhancedAgent

def _extract_sources_from_specialist(self, specialist_results: Dict[str, Any]) -> List[Dict[str, str]]:
    """Extract sources from specialist agent results."""
    sources = []
    source_counter = 1
    
    # Extract from research agent results
    if "primary_results" in specialist_results:
        for item in specialist_results["primary_results"]:
            if isinstance(item, dict) and 'url' in item and 'error' not in item:
                sources.append({
                    "id": source_counter,
                    "title": item.get("title", f"Source {source_counter}"),
                    "url": item.get("url"),
                    "type": "research",
                    "platform": ""
                })
                source_counter += 1
    
    # Extract from analysis agent results
    if "analysis_results" in specialist_results and "financial_analysis" in specialist_results["analysis_results"]:
        financial_data = specialist_results["analysis_results"]["financial_analysis"]
        if "symbol" in financial_data:
            sources.append({
                "id": source_counter,
                "title": f"Yahoo Finance - {financial_data['symbol']}",
                "url": f"https://finance.yahoo.com/quote/{financial_data['symbol']}",
                "type": "financial",
                "platform": "yahoo_finance"
            })
    
    return sources


class ConnectionManager:
    def __init__(self):
        self.conversations: Dict[str, List[Dict[str, str]]] = {}

    def get_history(self, client_id: str) -> List[Dict[str, str]]:
        return self.conversations.get(client_id, [])

    def add_to_history(self, client_id: str, user_message: str, ai_response: str):
        if client_id not in self.conversations:
            self.conversations[client_id] = []
        self.conversations[client_id].append({"role": "user", "content": user_message})
        self.conversations[client_id].append({"role": "assistant", "content": ai_response})

    def clear_history(self, client_id: str):
        if client_id in self.conversations:
            del self.conversations[client_id]

manager = ConnectionManager()
agent = EnhancedAgent()  # Use the enhanced agent

# --- FLASK ROUTES ---

@app.route("/")
def index():
    return render_template('index.html')

@app.route("/health")
def health():
    return jsonify({
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "version": "2.0.0",
        "features": [
            "Enhanced Web Search with Language Filtering",
            "Social Media Search Tool", 
            "Enhanced News Search",
            "Improved Financial Data",
            "Better Error Handling",
            "Casual Conversation Detection"
        ]
    })

# --- SOCKETIO EVENTS ---

@socketio.on('connect')
def handle_connect():
    client_id = request.sid
    logging.info(f"Client {client_id} connected.")
    emit('connected', {"client_id": client_id, "message": "Connected to Enhanced Agentic AI"})

@socketio.on('disconnect')
def handle_disconnect():
    client_id = request.sid
    logging.info(f"Client {client_id} disconnected.")

@socketio.on('send_message')
def handle_message(data):
    client_id = request.sid
    user_message = data.get('message', '').strip()
    
    if not user_message:
        emit('error', {"message": "Empty message received."})
        return

    logging.info(f"Received message from {client_id}: {user_message}")

    # Get conversation history
    conversation_history = manager.get_history(client_id)

    # Run the enhanced agent in a separate thread
    def run_agent():
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            result = loop.run_until_complete(agent.run(client_id, user_message, conversation_history))
            # Add to conversation history
            manager.add_to_history(client_id, user_message, result.get("response", ""))
        except Exception as e:
            logging.error(f"Error processing message: {e}")
            socketio.emit('error', {"message": f"Error processing your request: {str(e)}"}, room=client_id)
        finally:
            loop.close()

    # Start the agent in a background thread
    thread = threading.Thread(target=run_agent)
    thread.daemon = True
    thread.start()

@socketio.on('clear_history')
def handle_clear_history():
    client_id = request.sid
    manager.clear_history(client_id)
    emit('history_cleared', {"message": "Conversation history cleared."})
    logging.info(f"Cleared conversation history for client {client_id}")

@socketio.on('get_history')
def handle_get_history():
    client_id = request.sid
    history = manager.get_history(client_id)
    emit('conversation_history', {"history": history})

# --- RUN THE APP ---

if __name__ == '__main__':
    print("=" * 70)
    print("🚀 Starting Enhanced Agentic AI Flask Server...")
    print("=" * 70)
    print("📍 Server running at: http://localhost:5000")
    print("🔗 WebSocket endpoint: ws://localhost:5000/socket.io/")
    print("💡 Enhanced Features:")
    print("  ✅ Language-filtered web search")
    print("  ✅ Social media specific search tool")
    print("  ✅ Enhanced news search")
    print("  ✅ Improved financial data fetching")
    print("  ✅ Better error handling and fallbacks")
    print("  ✅ Query classification and routing")
    print("  ✅ Casual conversation detection")
    print("  ✅ Source quality filtering")
    print("=" * 70)

    # Install required packages if missing
    try:
        import flask_cors
    except ImportError:
        print("⚠️ Installing missing flask-cors...")
        os.system("pip install flask-cors")

    # Run with SocketIO
    socketio.run(
        app,
        host='0.0.0.0',
        port=5000,
        debug=True,
        allow_unsafe_werkzeug=True
    )
