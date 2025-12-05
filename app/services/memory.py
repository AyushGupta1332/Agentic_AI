import logging
from datetime import datetime, timezone
from typing import Dict, Any, List
import chromadb
from chromadb.utils import embedding_functions
from config import CHROMA_DB_PATH, EMBEDDING_MODEL

# Initialize ChromaDB
try:
    chroma_client = chromadb.PersistentClient(path=CHROMA_DB_PATH)
    embedding_function = embedding_functions.SentenceTransformerEmbeddingFunction(model_name=EMBEDDING_MODEL)
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
            "timestamp": datetime.now(timezone.utc).isoformat(),
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

class MemoryService:
    """Service for managing the agent's memory using ChromaDB."""
    
    def add_to_memory(self, user_id: str, query: str, response: str):
        if not memory_collection:
            return
        logging.info("Adding interaction to memory.")
        try:
            document = f"User query: {query}\nAI response: {response}"
            doc_id = f"{user_id}-{datetime.now(timezone.utc).isoformat()}"
            memory_collection.add(
                documents=[document],
                metadatas=[{"user_id": user_id, "timestamp": datetime.now(timezone.utc).timestamp()}],
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
            return []

    def get_recent_history(self, user_id: str, limit: int = 10) -> List[Dict[str, str]]:
        if not memory_collection:
            return []
        try:
            # Get all documents for the user
            results = memory_collection.get(
                where={"user_id": user_id},
                include=["metadatas", "documents"]
            )
            
            if not results['ids']:
                return []
            
            # Combine into a list of (timestamp, document)
            history_items = []
            for i, doc in enumerate(results['documents']):
                meta = results['metadatas'][i]
                timestamp = meta.get('timestamp', 0)
                history_items.append((timestamp, doc))
            
            # Sort by timestamp
            history_items.sort(key=lambda x: x[0])
            
            # Take the last 'limit' items
            recent_items = history_items[-limit:]
            
            # Parse documents back into role/content format
            formatted_history = []
            for _, doc in recent_items:
                # Assuming doc format: "User query: {query}\nAI response: {response}"
                parts = doc.split("\nAI response: ")
                if len(parts) == 2:
                    query_part = parts[0].replace("User query: ", "")
                    response_part = parts[1]
                    formatted_history.append({"role": "user", "content": query_part})
                    formatted_history.append({"role": "assistant", "content": response_part})
            
            return formatted_history
            
        except Exception as e:
            logging.error(f"Error retrieving history: {e}")
            return []
