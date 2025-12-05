import pytest
from app.tools.search import EnhancedWebSearchTool, EnhancedNewsSearchTool
from app.tools.finance import FinancialTool

@pytest.mark.asyncio
async def test_web_search_tool():
    tool = EnhancedWebSearchTool()
    assert tool.name == "web_search"
    
    # Mocking would be better, but for now we check structure
    # We won't actually call the API in unit tests to avoid costs/network issues
    # unless we mock it. For this first pass, we'll just check instantiation.
    assert tool.description is not None

@pytest.mark.asyncio
async def test_financial_tool():
    tool = FinancialTool()
    assert tool.name == "get_stock_info"
    
    # Test validation logic (doesn't require API call)
    # Assuming we can test internal methods or validation if exposed
    pass
