import logging
import json
import asyncio
from datetime import datetime
from typing import List, Dict, Any
from groq import AsyncGroq
from config import GROQ_API_KEY

from app.tools.search import EnhancedWebSearchTool, EnhancedNewsSearchTool, SocialMediaSearchTool
from app.tools.finance import FinancialTool
from app.tools.discovery import DynamicToolDiscovery
from app.services.query_analysis import EnhancedQueryAnalysisService
from app.services.synthesis import InformationProcessingService
from app.services.memory import MemoryService, ConversationMemoryManager
from app.services.proactive import ProactiveTaskManager
from app.services.response import AdaptiveResponseGenerator
from app.services.processing import RealTimeDataStream
from app.services.analytics import AdvancedAnalyticsEngine
from app.services.cache import IntelligentCache
from app.agents.orchestrator import AgentOrchestrator
from app.utils.helpers import make_json_serializable

class EnhancedAgent:
    """Enhanced main agent with multi-agent orchestration and advanced systems."""
    
    def __init__(self):
        self.groq_client = AsyncGroq(api_key=GROQ_API_KEY)
        self.tools = [
            EnhancedWebSearchTool(),
            EnhancedNewsSearchTool(),
            SocialMediaSearchTool(),
            FinancialTool()
        ]
        self.analysis_service = EnhancedQueryAnalysisService(self.tools, self.groq_client)
        self.processing_service = InformationProcessingService(self.groq_client)
        self.memory_service = MemoryService()
        self.tool_mapping = {tool.name: tool for tool in self.tools}
        
        # Multi-agent orchestrator
        self.agent_orchestrator = AgentOrchestrator()
        
        # Enhanced memory and learning systems
        self.conversation_memory = ConversationMemoryManager()
        self.proactive_manager = ProactiveTaskManager()
        self.adaptive_generator = AdaptiveResponseGenerator(self.groq_client)
        
        # NEW: Advanced systems
        self.data_streams = RealTimeDataStream()
        self.tool_discovery = DynamicToolDiscovery(self.groq_client)
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

    async def run(self, user_id: str, query: str, conversation_history: List[Dict[str, str]], socketio):
        start_time = datetime.utcnow()
        
        # Load history from persistent memory if empty (handles server restarts)
        if not conversation_history and self.memory_service:
            try:
                persistent_history = self.memory_service.get_recent_history(user_id)
                if persistent_history:
                    conversation_history = persistent_history
                    logging.info(f"📜 Loaded {len(conversation_history)} turns from persistent memory")
            except Exception as e:
                logging.warning(f"Failed to load persistent history: {e}")
        
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
                if self.memory_service:
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

        if self.memory_service:
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
