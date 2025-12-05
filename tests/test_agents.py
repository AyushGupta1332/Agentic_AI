import pytest
from app.agents.research import ResearchAgent
from app.agents.analysis import AnalysisAgent

@pytest.mark.asyncio
async def test_research_agent_capabilities():
    agent = ResearchAgent()
    assert agent.name == "ResearchAgent"
    
    # Test can_handle
    assert await agent.can_handle("research the history of AI") is True
    assert await agent.can_handle("find information about python") is True
    assert await agent.can_handle("what is the weather") is True # 'what is' is a keyword

@pytest.mark.asyncio
async def test_analysis_agent_capabilities():
    agent = AnalysisAgent()
    assert agent.name == "AnalysisAgent"
    
    # Test can_handle
    assert await agent.can_handle("analyze the data") is True
    assert await agent.can_handle("compare stock prices") is True
    assert await agent.can_handle("hello") is False # Should be false
