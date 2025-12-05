import logging
from datetime import datetime
from typing import Dict, Any, List

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
