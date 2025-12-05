from typing import Any, Dict

class BaseTool:
    """Base class for all tools."""
    def __init__(self, name: str, description: str):
        self.name = name
        self.description = description

    async def execute(self, **kwargs) -> Any:
        raise NotImplementedError("Each tool must implement the execute method.")
