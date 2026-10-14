from typing import List, Dict, Any, Optional, Literal
from pydantic import BaseModel, Field
from datetime import datetime, timezone

class MCPServerConfig(BaseModel):
    name: str
    description: Optional[str] = ""
    transport: Literal["stdio", "http", "sse", "builtin"] = "stdio"
    category: Optional[str] = "custom"  # "wordpress", "vps", "github", "custom"
    command: Optional[str] = None
    args: List[str] = Field(default_factory=list)
    env: Dict[str, str] = Field(default_factory=dict)
    url: Optional[str] = None
    headers: Dict[str, str] = Field(default_factory=dict)
    enabled: bool = True
    status: str = "configured"  # "connected", "error", "disabled", "configured"
    last_tested: Optional[str] = None
    last_error: Optional[str] = None
    tools: List[Dict[str, Any]] = Field(default_factory=list)

class MCPToolCallRequest(BaseModel):
    server: str
    tool: str
    arguments: Dict[str, Any] = Field(default_factory=dict)
