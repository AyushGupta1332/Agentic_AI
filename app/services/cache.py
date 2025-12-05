from datetime import datetime, timezone
from typing import Dict, Any, Optional, List

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
            "timestamp": datetime.now(timezone.utc).timestamp(),
            "ttl": ttl,
            "access_count": 1
        }
        
        self._track_access(key)

    def _track_access(self, key: str):
        """Track access patterns for predictive caching."""
        if key not in self.access_patterns:
            self.access_patterns[key] = []
        
        self.access_patterns[key].append(datetime.now(timezone.utc).timestamp())
        
        # Keep only recent access history
        cutoff = datetime.now(timezone.utc).timestamp() - 86400  # 24 hours
        self.access_patterns[key] = [t for t in self.access_patterns[key] if t > cutoff]
    
    def _is_fresh(self, cache_entry: Dict[str, Any]) -> bool:
        """Check if cache entry is still fresh."""
        age = datetime.now(timezone.utc).timestamp() - cache_entry["timestamp"]
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
                    time_since_last = datetime.now(timezone.utc).timestamp() - accesses[-1]
                    if time_since_last > avg_interval * 0.8:
                        predictions.append(key)
        
        return predictions[:5]  # Return top 5 predictions
