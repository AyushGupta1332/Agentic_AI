import pytest
from app.services.memory import ConversationMemoryManager
from app.services.cache import IntelligentCache

def test_memory_manager():
    manager = ConversationMemoryManager()
    
    # Test topic extraction
    topics = manager._extract_topics("Tell me about AI and python")
    assert "technology" in topics
    
    topics = manager._extract_topics("How is the stock market?")
    assert "business" in topics
    
    # Test complexity assessment
    score = manager._assess_complexity("Simple query")
    assert score < 5
    
    score = manager._assess_complexity("Analyze and compare the algorithmic complexity of these two functions with optimization in mind?")
    assert score > 3

def test_intelligent_cache():
    cache = IntelligentCache(max_size=10)
    
    # Test set and get
    cache.set("key1", "value1")
    assert cache.get("key1") == "value1"
    
    # Test miss
    assert cache.get("key2") is None
    
    # Test eviction (simplified)
    for i in range(15):
        cache.set(f"key{i}", f"value{i}")
    
    assert len(cache.cache) <= 10
