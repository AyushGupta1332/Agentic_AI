from typing import List, Dict, Any
from pydantic import BaseModel

class ToolCall(BaseModel):
    name: str
    parameters: Dict[str, Any]

class AgentAction(BaseModel):
    tool_calls: List[ToolCall]
    log: str
