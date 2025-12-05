import asyncio
import logging
from datetime import datetime
from typing import Dict, Any
from app.tools.search import EnhancedNewsSearchTool

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
