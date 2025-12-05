from typing import List, Dict, Any

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
