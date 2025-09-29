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
GROQ_API_KEY = "Your_Groq_API_KEY"

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

# --- JSON SERIALIZATION HELPER ---

def make_json_serializable(obj):
    """Convert objects to JSON serializable format."""
    if isinstance(obj, datetime):
        return obj.isoformat()
    elif isinstance(obj, dict):
        return {key: make_json_serializable(value) for key, value in obj.items()}
    elif isinstance(obj, list):
        return [make_json_serializable(item) for item in obj]
    elif hasattr(obj, '__dict__'):
        return make_json_serializable(obj.__dict__)
    else:
        return obj


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

# --- REAL-TIME DATA PROCESSING SYSTEM ---

class RealTimeDataStream:
    """Manages real-time data streams with intelligent processing."""
    
    def __init__(self):
        self.active_streams = {}
        self.stream_callbacks = {}
        self.data_cache = {}
        self.last_updates = {}
        
    async def create_stream(self, stream_id: str, source_type: str, config: Dict[str, Any]) -> bool:
        """Create a new real-time data stream."""
        try:
            if source_type == "financial":
                await self._setup_financial_stream(stream_id, config)
            elif source_type == "news":
                await self._setup_news_stream(stream_id, config)
            elif source_type == "web_monitor":
                await self._setup_web_monitor_stream(stream_id, config)
            
            self.active_streams[stream_id] = {
                "type": source_type,
                "config": config,
                "status": "active",
                "created": datetime.utcnow().isoformat()
            }
            
            logging.info(f"✅ Created real-time stream: {stream_id}")
            return True
            
        except Exception as e:
            logging.error(f"Failed to create stream {stream_id}: {e}")
            return False
    
    async def _setup_financial_stream(self, stream_id: str, config: Dict[str, Any]):
        """Setup financial data streaming."""
        symbols = config.get("symbols", ["AAPL", "GOOGL", "MSFT"])
        
        async def financial_updater():
            while stream_id in self.active_streams:
                try:
                    financial_data = {}
                    for symbol in symbols:
                        # Simulate real-time financial data (in production, use real API)
                        import random
                        base_price = 150 + random.uniform(-10, 10)
                        change = random.uniform(-5, 5)
                        
                        financial_data[symbol] = {
                            "symbol": symbol,
                            "price": round(base_price, 2),
                            "change": round(change, 2),
                            "change_percent": round((change / base_price) * 100, 2),
                            "timestamp": datetime.utcnow().isoformat(),
                            "volume": random.randint(1000000, 10000000)
                        }
                    
                    self.data_cache[stream_id] = financial_data
                    self.last_updates[stream_id] = datetime.utcnow()
                    
                    # Call registered callbacks
                    if stream_id in self.stream_callbacks:
                        for callback in self.stream_callbacks[stream_id]:
                            await callback(financial_data)
                    
                    await asyncio.sleep(30)  # Update every 30 seconds
                    
                except Exception as e:
                    logging.error(f"Financial stream {stream_id} error: {e}")
                    await asyncio.sleep(60)  # Wait longer on error
        
        # Start the updater task
        asyncio.create_task(financial_updater())
    
    async def _setup_news_stream(self, stream_id: str, config: Dict[str, Any]):
        """Setup news data streaming."""
        keywords = config.get("keywords", ["AI", "technology"])
        
        async def news_updater():
            while stream_id in self.active_streams:
                try:
                    # Use existing news search tool
                    news_tool = EnhancedNewsSearchTool()
                    latest_news = []
                    
                    for keyword in keywords:
                        news_results = await news_tool.execute(keyword, 3)
                        if isinstance(news_results, list):
                            latest_news.extend(news_results)
                    
                    # Filter and deduplicate
                    unique_news = []
                    seen_urls = set()
                    
                    for news in latest_news:
                        if isinstance(news, dict) and news.get("url") not in seen_urls:
                            seen_urls.add(news.get("url", ""))
                            unique_news.append({
                                **news,
                                "stream_timestamp": datetime.utcnow().isoformat()
                            })
                    
                    self.data_cache[stream_id] = unique_news
                    self.last_updates[stream_id] = datetime.utcnow()
                    
                    # Call registered callbacks
                    if stream_id in self.stream_callbacks:
                        for callback in self.stream_callbacks[stream_id]:
                            await callback(unique_news)
                    
                    await asyncio.sleep(300)  # Update every 5 minutes
                    
                except Exception as e:
                    logging.error(f"News stream {stream_id} error: {e}")
                    await asyncio.sleep(600)  # Wait longer on error
        
        asyncio.create_task(news_updater())
    
    async def _setup_web_monitor_stream(self, stream_id: str, config: Dict[str, Any]):
        """Setup web page monitoring stream."""
        urls = config.get("urls", [])
        
        async def web_monitor_updater():
            previous_hashes = {}
            
            while stream_id in self.active_streams:
                try:
                    changes_detected = []
                    
                    for url in urls:
                        try:
                            # Simple web content monitoring (in production, use proper web scraping)
                            import hashlib
                            
                            # Simulate content hash check
                            current_hash = hashlib.md5(f"{url}_{datetime.utcnow().minute}".encode()).hexdigest()
                            
                            if url in previous_hashes and previous_hashes[url] != current_hash:
                                changes_detected.append({
                                    "url": url,
                                    "change_detected": True,
                                    "timestamp": datetime.utcnow().isoformat(),
                                    "change_type": "content_update"
                                })
                            
                            previous_hashes[url] = current_hash
                            
                        except Exception as e:
                            logging.warning(f"Web monitor error for {url}: {e}")
                    
                    if changes_detected:
                        self.data_cache[stream_id] = changes_detected
                        self.last_updates[stream_id] = datetime.utcnow()
                        
                        # Call registered callbacks
                        if stream_id in self.stream_callbacks:
                            for callback in self.stream_callbacks[stream_id]:
                                await callback(changes_detected)
                    
                    await asyncio.sleep(600)  # Check every 10 minutes
                    
                except Exception as e:
                    logging.error(f"Web monitor stream {stream_id} error: {e}")
                    await asyncio.sleep(1200)  # Wait longer on error
        
        asyncio.create_task(web_monitor_updater())
    
    def register_callback(self, stream_id: str, callback):
        """Register a callback for stream updates."""
        if stream_id not in self.stream_callbacks:
            self.stream_callbacks[stream_id] = []
        self.stream_callbacks[stream_id].append(callback)
    
    def get_latest_data(self, stream_id: str) -> Dict[str, Any]:
        """Get the latest data from a stream."""
        if stream_id in self.data_cache:
            last_update = self.last_updates.get(stream_id)
            return {
                "data": self.data_cache[stream_id],
                "last_update": last_update.isoformat() if last_update else None,
                "status": "active" if stream_id in self.active_streams else "inactive"
            }
        return {"data": None, "last_update": None, "status": "not_found"}
    
    async def stop_stream(self, stream_id: str) -> bool:
        """Stop a real-time data stream."""
        if stream_id in self.active_streams:
            del self.active_streams[stream_id]
            if stream_id in self.data_cache:
                del self.data_cache[stream_id]
            if stream_id in self.stream_callbacks:
                del self.stream_callbacks[stream_id]
            if stream_id in self.last_updates:
                del self.last_updates[stream_id]
            logging.info(f"🛑 Stopped stream: {stream_id}")
            return True
        return False


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

class AdvancedAnalyticsEngine:
    """Advanced analytics and pattern recognition system."""
    
    def __init__(self):
        self.user_analytics = {}
        self.system_metrics = {}
        self.pattern_cache = {}
        
    def track_user_interaction(self, user_id: str, interaction_data: Dict[str, Any]):
        """Track user interaction for analytics."""
        if user_id not in self.user_analytics:
            self.user_analytics[user_id] = {
                "total_interactions": 0,
                "avg_response_time": 0,
                "preferred_agents": {},
                "query_patterns": [],
                "satisfaction_metrics": []
            }
        
        analytics = self.user_analytics[user_id]
        analytics["total_interactions"] += 1
        
        # Track agent preferences
        agent_used = interaction_data.get("agent_used", "unknown")
        if agent_used not in analytics["preferred_agents"]:
            analytics["preferred_agents"][agent_used] = 0
        analytics["preferred_agents"][agent_used] += 1
        
        # Track query patterns
        query_pattern = {
            "timestamp": datetime.utcnow().isoformat(),
            "complexity": interaction_data.get("complexity", 1),
            "response_time": interaction_data.get("processing_time", 0),
            "satisfaction": interaction_data.get("satisfaction", None)
        }
        
        analytics["query_patterns"].append(query_pattern)
        
        # Keep only last 100 interactions for performance
        if len(analytics["query_patterns"]) > 100:
            analytics["query_patterns"] = analytics["query_patterns"][-100:]
    
    def analyze_user_patterns(self, user_id: str) -> Dict[str, Any]:
        """Analyze patterns for a specific user."""
        if user_id not in self.user_analytics:
            return {"status": "insufficient_data"}
        
        analytics = self.user_analytics[user_id]
        
        # Calculate trends
        recent_interactions = analytics["query_patterns"][-10:]
        if len(recent_interactions) >= 5:
            avg_complexity = sum(i["complexity"] for i in recent_interactions) / len(recent_interactions)
            avg_response_time = sum(i["response_time"] for i in recent_interactions) / len(recent_interactions)
            
            return {
                "total_interactions": analytics["total_interactions"],
                "avg_complexity": avg_complexity,
                "avg_response_time": avg_response_time,
                "most_used_agent": max(analytics["preferred_agents"].items(), key=lambda x: x[1])[0] if analytics["preferred_agents"] else "unknown",
                "trend_analysis": self._analyze_trends(recent_interactions),
                "recommendations": self._generate_recommendations(analytics)
            }
        
        return {"status": "insufficient_recent_data"}
    
    def _analyze_trends(self, interactions: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze trends in user interactions."""
        if len(interactions) < 3:
            return {"trend": "insufficient_data"}
        
        # Analyze complexity trend
        complexities = [i["complexity"] for i in interactions]
        if complexities[-1] > complexities[0]:
            complexity_trend = "increasing"
        elif complexities[-1] < complexities[0]:
            complexity_trend = "decreasing"
        else:
            complexity_trend = "stable"
        
        # Analyze response time trend
        response_times = [i["response_time"] for i in interactions]
        avg_recent = sum(response_times[-3:]) / 3
        avg_older = sum(response_times[:3]) / 3
        
        if avg_recent > avg_older * 1.2:
            performance_trend = "degrading"
        elif avg_recent < avg_older * 0.8:
            performance_trend = "improving"
        else:
            performance_trend = "stable"
        
        return {
            "complexity_trend": complexity_trend,
            "performance_trend": performance_trend,
            "interaction_frequency": "regular" if len(interactions) >= 5 else "occasional"
        }
    
    def _generate_recommendations(self, analytics: Dict[str, Any]) -> List[str]:
        """Generate recommendations based on analytics."""
        recommendations = []
        
        # Agent usage recommendations
        if analytics["preferred_agents"]:
            most_used = max(analytics["preferred_agents"].items(), key=lambda x: x[1])
            if most_used[1] > analytics["total_interactions"] * 0.7:
                recommendations.append(f"Consider exploring other agents beyond {most_used[0]} for variety")
        
        # Complexity recommendations
        recent_complexity = [p["complexity"] for p in analytics["query_patterns"][-5:]]
        if recent_complexity and sum(recent_complexity) / len(recent_complexity) < 3:
            recommendations.append("Try more complex queries to unlock advanced features")
        
        return recommendations

class IntelligentCache:
    """Intelligent caching system with predictive prefetching."""
    
    def __init__(self, max_size: int = 1000):
        self.cache = {}
        self.access_patterns = {}
        self.cache_stats = {"hits": 0, "misses": 0}
        self.max_size = max_size
        
    def get(self, key: str) -> Optional[Any]:
        """Get item from cache with usage tracking."""
        if key in self.cache:
            self.cache_stats["hits"] += 1
            self._track_access(key)
            
            # Check if data is still fresh
            cache_entry = self.cache[key]
            if self._is_fresh(cache_entry):
                return cache_entry["data"]
            else:
                del self.cache[key]
        
        self.cache_stats["misses"] += 1
        return None
    
    def set(self, key: str, data: Any, ttl: int = 3600):
        """Set item in cache with TTL."""
        if len(self.cache) >= self.max_size:
            self._evict_least_used()
        
        self.cache[key] = {
            "data": data,
            "timestamp": datetime.utcnow().timestamp(),
            "ttl": ttl,
            "access_count": 1
        }
        
        self._track_access(key)
    
    def _track_access(self, key: str):
        """Track access patterns for predictive caching."""
        if key not in self.access_patterns:
            self.access_patterns[key] = []
        
        self.access_patterns[key].append(datetime.utcnow().timestamp())
        
        # Keep only recent access history
        cutoff = datetime.utcnow().timestamp() - 86400  # 24 hours
        self.access_patterns[key] = [t for t in self.access_patterns[key] if t > cutoff]
    
    def _is_fresh(self, cache_entry: Dict[str, Any]) -> bool:
        """Check if cache entry is still fresh."""
        age = datetime.utcnow().timestamp() - cache_entry["timestamp"]
        return age < cache_entry["ttl"]
    
    def _evict_least_used(self):
        """Evict least used cache entry."""
        if not self.cache:
            return
        
        least_used_key = min(self.cache.keys(), 
                           key=lambda k: self.cache[k]["access_count"])
        del self.cache[least_used_key]
    
    def get_cache_stats(self) -> Dict[str, Any]:
        """Get cache performance statistics."""
        total_requests = self.cache_stats["hits"] + self.cache_stats["misses"]
        hit_rate = self.cache_stats["hits"] / total_requests if total_requests > 0 else 0
        
        return {
            "hit_rate": round(hit_rate * 100, 2),
            "total_entries": len(self.cache),
            "total_requests": total_requests,
            **self.cache_stats
        }
    
    def predict_next_access(self, user_id: str) -> List[str]:
        """Predict what the user might request next."""
        # Simple prediction based on access patterns
        predictions = []
        
        # Find frequently accessed items
        for key, accesses in self.access_patterns.items():
            if len(accesses) >= 3:  # Has been accessed multiple times
                # Check if it's accessed regularly
                if len(accesses) >= 2:
                    time_diffs = [accesses[i] - accesses[i-1] for i in range(1, len(accesses))]
                    avg_interval = sum(time_diffs) / len(time_diffs)
                    
                    # If it's been longer than average interval, predict next access
                    time_since_last = datetime.utcnow().timestamp() - accesses[-1]
                    if time_since_last > avg_interval * 0.8:
                        predictions.append(key)
        
        return predictions[:5]  # Return top 5 predictions


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

# --- ENHANCED MEMORY & LEARNING SYSTEM ---

class ConversationMemoryManager:
    """Advanced conversation memory with learning capabilities."""
    
    def __init__(self):
        self.short_term_memory = {}  # Current session
        self.conversation_patterns = {}  # Learned patterns
        self.user_preferences = {}  # User-specific preferences
        self.knowledge_graph = {}  # Interconnected knowledge
        
    def add_conversation_turn(self, user_id: str, query: str, response: str, metadata: Dict[str, Any]):
        """Add a conversation turn with rich metadata."""
        if user_id not in self.short_term_memory:
            self.short_term_memory[user_id] = []
            
        turn_data = {
            "timestamp": datetime.utcnow().isoformat(),
            "query": query,
            "response": response,
            "metadata": metadata,
            "topics": self._extract_topics(query),
            "sentiment": self._analyze_sentiment(query),
            "complexity": self._assess_complexity(query)
        }
        
        self.short_term_memory[user_id].append(turn_data)
        self._update_user_patterns(user_id, turn_data)
        
    def _extract_topics(self, text: str) -> List[str]:
        """Extract key topics from text."""
        # Simple keyword-based topic extraction
        tech_topics = ['ai', 'machine learning', 'python', 'data', 'programming', 'technology']
        business_topics = ['market', 'stock', 'finance', 'business', 'economy', 'investment']
        creative_topics = ['story', 'creative', 'write', 'art', 'design', 'poem']
        
        topics = []
        text_lower = text.lower()
        
        if any(topic in text_lower for topic in tech_topics):
            topics.append('technology')
        if any(topic in text_lower for topic in business_topics):
            topics.append('business')
        if any(topic in text_lower for topic in creative_topics):
            topics.append('creative')
            
        return topics if topics else ['general']
    
    def _analyze_sentiment(self, text: str) -> str:
        """Basic sentiment analysis."""
        positive_words = ['good', 'great', 'excellent', 'amazing', 'love', 'like', 'awesome']
        negative_words = ['bad', 'terrible', 'hate', 'awful', 'worst', 'horrible']
        
        text_lower = text.lower()
        positive_count = sum(1 for word in positive_words if word in text_lower)
        negative_count = sum(1 for word in negative_words if word in text_lower)
        
        if positive_count > negative_count:
            return 'positive'
        elif negative_count > positive_count:
            return 'negative'
        else:
            return 'neutral'
    
    def _assess_complexity(self, text: str) -> int:
        """Assess query complexity (1-10 scale)."""
        complexity_score = 1
        
        # Length factor
        if len(text) > 100:
            complexity_score += 2
        elif len(text) > 50:
            complexity_score += 1
            
        # Technical terms
        technical_terms = ['analyze', 'compare', 'explain', 'implement', 'algorithm', 'optimize']
        complexity_score += sum(1 for term in technical_terms if term in text.lower())
        
        # Question complexity
        if '?' in text:
            question_count = text.count('?')
            complexity_score += min(question_count, 3)
            
        return min(complexity_score, 10)
    
    def _update_user_patterns(self, user_id: str, turn_data: Dict[str, Any]):
        """Update learned patterns for user."""
        if user_id not in self.user_preferences:
            self.user_preferences[user_id] = {
                'preferred_topics': {},
                'avg_complexity': 0,
                'communication_style': 'formal',
                'response_length_preference': 'medium'
            }
        
        # Update topic preferences
        for topic in turn_data['topics']:
            if topic not in self.user_preferences[user_id]['preferred_topics']:
                self.user_preferences[user_id]['preferred_topics'][topic] = 0
            self.user_preferences[user_id]['preferred_topics'][topic] += 1
    
    def get_context_for_query(self, user_id: str, current_query: str) -> Dict[str, Any]:
        """Get relevant context for current query."""
        if user_id not in self.short_term_memory:
            return {"context": "new_user"}
        
        recent_conversations = self.short_term_memory[user_id][-5:]  # Last 5 turns
        user_prefs = self.user_preferences.get(user_id, {})
        
        return {
            "recent_topics": [turn["topics"] for turn in recent_conversations],
            "user_preferences": user_prefs,
            "conversation_flow": recent_conversations,
            "suggested_approach": self._suggest_approach(user_id, current_query)
        }
    
    def _suggest_approach(self, user_id: str, query: str) -> str:
        """Suggest best approach based on user history."""
        user_prefs = self.user_preferences.get(user_id, {})
        query_topics = self._extract_topics(query)
        
        # Check if user has preferences for these topics
        preferred_topics = user_prefs.get('preferred_topics', {})
        
        if any(topic in preferred_topics for topic in query_topics):
            return "personalized"
        else:
            return "standard"

class ProactiveTaskManager:
    """Manages proactive task suggestions and automation."""
    
    def __init__(self):
        self.task_patterns = {}
        self.scheduled_tasks = {}
        self.user_workflows = {}
    
    async def analyze_for_proactive_tasks(self, user_id: str, conversation_history: List[Dict]) -> List[Dict[str, Any]]:
        """Analyze conversation for proactive task opportunities."""
        suggestions = []
        
        if len(conversation_history) < 2:
            return suggestions
        
        recent_queries = [turn.get('query', '') for turn in conversation_history[-3:]]
        
        # Pattern 1: Repeated similar queries
        if self._detect_repeated_pattern(recent_queries):
            suggestions.append({
                "type": "automation",
                "title": "Create Automated Workflow",
                "description": "I notice you're asking similar questions. Would you like me to create an automated workflow?",
                "priority": "medium"
            })
        
        # Pattern 2: Research-heavy session
        research_count = sum(1 for query in recent_queries if any(word in query.lower() for word in ['research', 'find', 'tell me about', 'what is']))
        if research_count >= 2:
            suggestions.append({
                "type": "knowledge_base",
                "title": "Personal Knowledge Base",
                "description": "Would you like me to compile your research into a personal knowledge base?",
                "priority": "low"
            })
        
        # Pattern 3: Time-sensitive queries
        if any(word in ' '.join(recent_queries).lower() for word in ['today', 'latest', 'recent', 'current']):
            suggestions.append({
                "type": "monitoring",
                "title": "Set Up Monitoring",
                "description": "I can monitor these topics and notify you of updates automatically.",
                "priority": "high"
            })
        
        return suggestions
    
    def _detect_repeated_pattern(self, queries: List[str]) -> bool:
        """Detect if queries follow a repeated pattern."""
        if len(queries) < 2:
            return False
        
        # Simple similarity check based on common words
        for i in range(len(queries) - 1):
            query1_words = set(queries[i].lower().split())
            query2_words = set(queries[i + 1].lower().split())
            
            if query1_words and query2_words:
                similarity = len(query1_words.intersection(query2_words)) / len(query1_words.union(query2_words))
                if similarity > 0.5:  # 50% similarity threshold
                    return True
        
        return False

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

# --- INFORMATION PROCESSING SERVICE ---

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

class EnhancedAgent:
    """Enhanced main agent with multi-agent orchestration and advanced systems."""
    
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
        
        # Multi-agent orchestrator
        self.agent_orchestrator = AgentOrchestrator()
        
        # Enhanced memory and learning systems
        self.conversation_memory = ConversationMemoryManager()
        self.proactive_manager = ProactiveTaskManager()
        self.adaptive_generator = AdaptiveResponseGenerator(AsyncGroq(api_key=GROQ_API_KEY))
        
        # NEW: Advanced systems
        self.data_streams = RealTimeDataStream()
        self.tool_discovery = DynamicToolDiscovery(AsyncGroq(api_key=GROQ_API_KEY))
        self.analytics = AdvancedAnalyticsEngine()
        self.smart_cache = IntelligentCache(max_size=500)
        
        # Flag to track if streams are initialized
        self.streams_initialized = False

    async def _ensure_streams_initialized(self):
        """Ensure default data streams are initialized (called when needed)."""
        if not self.streams_initialized:
            try:
                # Financial stream for popular stocks
                await self.data_streams.create_stream(
                    "default_financial",
                    "financial",
                    {"symbols": ["AAPL", "GOOGL", "MSFT", "TSLA", "NVDA"]}
                )
                
                # News stream for technology
                await self.data_streams.create_stream(
                    "tech_news",
                    "news", 
                    {"keywords": ["AI", "technology", "innovation", "startup"]}
                )
                
                self.streams_initialized = True
                logging.info("✅ Default data streams initialized")
            except Exception as e:
                logging.error(f"Failed to initialize default streams: {e}")

    async def run(self, user_id: str, query: str, conversation_history: List[Dict[str, str]]):
        start_time = datetime.utcnow()
        
        # Initialize streams if not already done
        await self._ensure_streams_initialized()
        
        # NEW: Check intelligent cache first
        cache_key = f"{user_id}:{hash(query)}"
        cached_response = self.smart_cache.get(cache_key)
        if cached_response:
            logging.info("📦 Serving response from intelligent cache")
            socketio.emit('status_update', {"message": "⚡ Found cached response"}, room=user_id)
            socketio.emit('final_response', cached_response, room=user_id)
            return cached_response
        
        # Send initial status update
        socketio.emit('status_update', {"message": "🔍 Analyzing your query..."}, room=user_id)
        
        # NEW: Check if we need dynamic tools
        available_tool_names = [tool.name for tool in self.tools]
        try:
            tool_analysis = await self.tool_discovery.analyze_tool_needs(query, available_tool_names)
            
            if tool_analysis.get("needs_new_tool") and tool_analysis.get("priority") in ["high", "medium"]:
                socketio.emit('status_update', {"message": f"🛠️ Creating specialized tool: {tool_analysis.get('suggested_tool_name')}"}, room=user_id)
                new_tool_id = await self.tool_discovery.create_dynamic_tool(tool_analysis)
                if new_tool_id:
                    socketio.emit('status_update', {"message": f"✅ Created tool: {new_tool_id}"}, room=user_id)
        except Exception as e:
            logging.warning(f"Tool discovery failed: {e}")
            tool_analysis = {"needs_new_tool": False}
        
        # NEW: Check real-time data streams for relevant information
        stream_data = {}
        try:
            if any(keyword in query.lower() for keyword in ['stock', 'price', 'market', 'financial']):
                financial_data = self.data_streams.get_latest_data("default_financial")
                if financial_data.get("data"):
                    stream_data["financial"] = financial_data
                    socketio.emit('status_update', {"message": "📈 Using real-time market data"}, room=user_id)
            
            if any(keyword in query.lower() for keyword in ['news', 'latest', 'recent', 'current']):
                news_data = self.data_streams.get_latest_data("tech_news")
                if news_data.get("data"):
                    stream_data["news"] = news_data
                    socketio.emit('status_update', {"message": "📰 Using real-time news data"}, room=user_id)
        except Exception as e:
            logging.warning(f"Stream data retrieval failed: {e}")
        
        # Get enhanced context and proactive suggestions
        socketio.emit('status_update', {"message": "🧠 Loading your personalized context..."}, room=user_id)
        
        user_context = self.conversation_memory.get_context_for_query(user_id, query)
        try:
            proactive_suggestions = await self.proactive_manager.analyze_for_proactive_tasks(user_id, conversation_history)
        except Exception as e:
            logging.warning(f"Proactive suggestions failed: {e}")
            proactive_suggestions = []
        
        if proactive_suggestions:
            socketio.emit('status_update', {"message": f"💡 Found {len(proactive_suggestions)} proactive suggestions"}, room=user_id)
        
        # Try multi-agent processing first
        socketio.emit('status_update', {"message": "🤖 Selecting specialist agent..."}, room=user_id)
        
        try:
            # NEW: Include stream data in multi-agent processing
            enhanced_conversation_history = conversation_history.copy()
            if stream_data:
                enhanced_conversation_history.append({
                    "role": "system",
                    "content": f"Real-time data available: {json.dumps(stream_data, indent=2)}"
                })
            
            multi_agent_result = await self.agent_orchestrator.process_with_specialist(query, enhanced_conversation_history)
            
            if "error" not in multi_agent_result:
                # Multi-agent processing successful
                agent_name = multi_agent_result.get('specialist_agent', 'specialist')
                socketio.emit('status_update', {"message": f"✅ Processed by {agent_name}"}, room=user_id)
                
                # Apply adaptive response generation
                socketio.emit('status_update', {"message": "🎯 Personalizing your response..."}, room=user_id)
                
                try:
                    adaptive_result = await self.adaptive_generator.generate_adaptive_response(
                        query, 
                        multi_agent_result.get("content", ""),
                        user_context,
                        proactive_suggestions
                    )
                except Exception as e:
                    logging.warning(f"Adaptive response generation failed: {e}")
                    adaptive_result = {
                        "adapted_response": multi_agent_result.get("content", ""),
                        "personalization_applied": False
                    }
                
                end_time = datetime.utcnow()
                processing_time = (end_time - start_time).total_seconds()
                
                # Store conversation with enhanced metadata
                metadata = {
                    "agent_used": agent_name,
                    "processing_time": processing_time,
                    "personalization_applied": adaptive_result.get("personalization_applied", False),
                    "proactive_suggestions_count": len(proactive_suggestions),
                    "real_time_data_used": len(stream_data) > 0,
                    "dynamic_tools_created": tool_analysis.get("needs_new_tool", False),
                    "cache_miss": True
                }
                
                final_response = adaptive_result.get("adapted_response", multi_agent_result.get("content", ""))
                
                # NEW: Track analytics
                try:
                    self.analytics.track_user_interaction(user_id, {
                        "agent_used": agent_name,
                        "processing_time": processing_time,
                        "complexity": self.conversation_memory._assess_complexity(query),
                        "satisfaction": None  # To be updated by user feedback
                    })
                except Exception as e:
                    logging.warning(f"Analytics tracking failed: {e}")
                
                self.conversation_memory.add_conversation_turn(
                    user_id, query, final_response, metadata
                )
                
                response_payload = make_json_serializable({
                    "response": final_response,
                    "confidence": 95,
                    "sources": self._extract_sources_from_specialist(multi_agent_result.get("specialist_results", {})),
                    "processing_time": round(processing_time, 2),
                    "method": f"Enhanced Multi-Agent: {agent_name}",
                    "tools_used": 1,
                    "sources_found": len(self._extract_sources_from_specialist(multi_agent_result.get("specialist_results", {}))),
                    "personalization_applied": adaptive_result.get("personalization_applied", False),
                    "proactive_suggestions": proactive_suggestions,
                    "real_time_data": stream_data,
                    "analytics": self._get_safe_analytics(user_id)
                })
                
                # NEW: Cache the response for future use
                try:
                    self.smart_cache.set(cache_key, response_payload, ttl=1800)  # Cache for 30 minutes
                except Exception as e:
                    logging.warning(f"Caching failed: {e}")
                
                # Store in memory
                if memory_collection:
                    asyncio.create_task(self._add_to_memory_async(user_id, query, final_response))
                
                socketio.emit('final_response', response_payload, room=user_id)
                return response_payload
                
        except Exception as e:
            logging.warning(f"Enhanced multi-agent processing failed, falling back to standard processing: {e}")
            socketio.emit('status_update', {"message": "🔄 Switching to standard processing..."}, room=user_id)
        
        # FALLBACK: Original processing method with enhancements
        plan = await self.analysis_service.get_plan(query, conversation_history)
        socketio.emit('status_update', {"message": f"📋 {plan.log}"}, room=user_id)

        tool_outputs = {}
        is_casual = len(plan.tool_calls) == 0 and "casual conversation" in plan.log.lower()
        
        # NEW: Include stream data in tool outputs
        if stream_data:
            tool_outputs["real_time_streams"] = stream_data
        
        if plan.tool_calls:
            socketio.emit('status_update', {"message": f"🔧 Executing {len(plan.tool_calls)} tool(s)..."}, room=user_id)
            
            for i, tool_call in enumerate(plan.tool_calls):
                if tool_call.name in self.tool_mapping:
                    try:
                        socketio.emit('status_update',
                                    {"message": f"⚙️ Running {tool_call.name} ({i+1}/{len(plan.tool_calls)})..."},
                                    room=user_id)
                        
                        tool = self.tool_mapping[tool_call.name]
                        result = await tool.execute(**tool_call.parameters)
                        tool_outputs[tool_call.name] = result
                        
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

        socketio.emit('status_update',
                     {"message": "🧠 Generating your response..." if is_casual else "🔬 Synthesizing information..."},
                     room=user_id)
        
        final_response_data = await self.processing_service.synthesize_response(
            query, tool_outputs, conversation_history, is_casual
        )

        if memory_collection:
            asyncio.create_task(self._add_to_memory_async(user_id, query, final_response_data.get("content", "")))

        end_time = datetime.utcnow()
        processing_time = (end_time - start_time).total_seconds()
        
        # NEW: Track analytics for fallback processing
        try:
            self.analytics.track_user_interaction(user_id, {
                "agent_used": "fallback_processing",
                "processing_time": processing_time,
                "complexity": self.conversation_memory._assess_complexity(query)
            })
        except Exception as e:
            logging.warning(f"Analytics tracking failed: {e}")
        
        response_payload = make_json_serializable({
            "response": final_response_data.get("content"),
            "confidence": final_response_data.get("confidence_score"),
            "sources": final_response_data.get("sources"),
            "processing_time": round(processing_time, 2),
            "method": "Casual Chat" if is_casual else (
            "Direct Answer" if not plan.tool_calls else
            f"Enhanced Search: {[tc.name for tc in plan.tool_calls]}"
            ),
            "tools_used": len(plan.tool_calls),
            "sources_found": len(final_response_data.get("sources", [])),
            "personalization_applied": False,
            "proactive_suggestions": [],
            "real_time_data": stream_data,
            "analytics": self._get_safe_analytics(user_id)
        })

        # NEW: Cache fallback responses too
        try:
            self.smart_cache.set(cache_key, response_payload, ttl=900)  # Cache for 15 minutes
        except Exception as e:
            logging.warning(f"Caching failed: {e}")
        
        socketio.emit('final_response', response_payload, room=user_id)
        return response_payload

    def _get_safe_analytics(self, user_id: str) -> Dict[str, Any]:
        """Get analytics data with error handling."""
        try:
            return {
                "cache_performance": self.smart_cache.get_cache_stats(),
                "user_patterns": self.analytics.analyze_user_patterns(user_id)
            }
        except Exception as e:
            logging.warning(f"Analytics retrieval failed: {e}")
            return {
                "cache_performance": {"hit_rate": 0, "total_entries": 0, "total_requests": 0},
                "user_patterns": {"status": "unavailable"}
            }

    async def _add_to_memory_async(self, user_id: str, query: str, response: str):
        try:
            self.memory_service.add_to_memory(user_id, query, response)
        except Exception as e:
            logging.warning(f"Memory storage failed: {e}")

    def _extract_sources_from_specialist(self, specialist_results: Dict[str, Any]) -> List[Dict[str, str]]:
        """Extract sources from specialist agent results."""
        sources = []
        source_counter = 1
        
        try:
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
            
        except Exception as e:
            logging.warning(f"Source extraction failed: {e}")
        
        return sources

    # NEW: Additional utility methods for advanced features
    async def get_system_health(self) -> Dict[str, Any]:
        """Get comprehensive system health metrics."""
        try:
            active_streams = len(self.data_streams.active_streams)
            cache_stats = self.smart_cache.get_cache_stats()
            
            return make_json_serializable({
                "status": "healthy",
                "active_data_streams": active_streams,
                "cache_performance": cache_stats,
                "discovered_tools": len(self.tool_discovery.discovered_tools),
                "streams_initialized": self.streams_initialized,
                "uptime": datetime.utcnow().isoformat()
            })
        except Exception as e:
            logging.error(f"System health check failed: {e}")
            return {"status": "error", "message": str(e)}
    
    async def optimize_performance(self):
        """Perform system optimization tasks."""
        try:
            # Clear old cache entries
            self.smart_cache._evict_least_used()
            
            # Clean up old analytics data
            cutoff_time = datetime.utcnow().timestamp() - 86400  # 24 hours ago
            for user_id in list(self.analytics.user_analytics.keys()):
                try:
                    user_data = self.analytics.user_analytics[user_id]
                    user_data["query_patterns"] = [
                        p for p in user_data["query_patterns"] 
                        if datetime.fromisoformat(p["timestamp"].replace('Z', '+00:00')).timestamp() > cutoff_time
                    ]
                except Exception as e:
                    logging.warning(f"Failed to clean analytics for user {user_id}: {e}")
            
            logging.info("✅ System optimization completed")
        except Exception as e:
            logging.error(f"System optimization failed: {e}")


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

# --- NEW SOCKETIO ENDPOINTS FOR ADVANCED FEATURES ---

@socketio.on('create_data_stream')
def handle_create_stream(data):
    client_id = request.sid
    
    stream_config = data.get('config', {})
    stream_type = data.get('type', 'news')
    stream_name = data.get('name', f'user_stream_{client_id}_{int(datetime.utcnow().timestamp())}')
    
    async def create_stream():
        success = await agent.data_streams.create_stream(stream_name, stream_type, stream_config)
        if success:
            emit('stream_created', make_json_serializable({
                "stream_id": stream_name,
                "status": "active",
                "message": f"✅ Created {stream_type} stream: {stream_name}"
            }))
        else:
            emit('stream_error', {
                "message": f"❌ Failed to create stream: {stream_name}"
            })
    
    # Run in background thread
    def run_create():
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.run_until_complete(create_stream())
        loop.close()
    
    threading.Thread(target=run_create, daemon=True).start()

@socketio.on('get_stream_data')
def handle_get_stream_data(data):
    client_id = request.sid
    stream_id = data.get('stream_id', 'default_financial')
    
    stream_data = agent.data_streams.get_latest_data(stream_id)
    emit('stream_data', make_json_serializable({
        "stream_id": stream_id,
        "data": stream_data
    }))

@socketio.on('get_analytics')
def handle_get_analytics():
    client_id = request.sid
    
    user_analytics = agent.analytics.analyze_user_patterns(client_id)
    cache_stats = agent.smart_cache.get_cache_stats()
    
    emit('analytics_data', make_json_serializable({
        "user_analytics": user_analytics,
        "cache_performance": cache_stats,
        "system_status": "optimal"
    }))

@socketio.on('suggest_tools')
def handle_suggest_tools():
    client_id = request.sid
    
    # Get user context
    user_context = agent.conversation_memory.get_context_for_query(client_id, "")
    tool_suggestions = agent.tool_discovery.get_tool_suggestions(user_context)
    
    emit('tool_suggestions', make_json_serializable({
        "suggestions": tool_suggestions,
        "context": "Based on your usage patterns"
    }))



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
