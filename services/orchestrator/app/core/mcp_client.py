"""
Nexus MCP Client Manager
========================

Manages connections to multiple MCP servers over SSE and aggregates tools
for use with LangGraph orchestration.

This module provides:
- Connection management for multiple MCP servers
- Tool discovery and aggregation
- LangChain tool binding
- Graceful error handling for offline servers

Author: Nexus Team
Version: 3.0.0
"""

import asyncio
import json
import logging
from datetime import datetime
from typing import Any, Callable, Dict, List, Optional, Union

import httpx
from pydantic import BaseModel, Field
from langchain_core.tools import BaseTool, StructuredTool

# Add shared lib to path
import os
import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../../shared")))

from nexus_lib.config import ConfigManager, ConfigKeys, AgentRegistry

logger = logging.getLogger("nexus.mcp_client")


# =============================================================================
# Data Models
# =============================================================================

class MCPToolDefinition(BaseModel):
    """Definition of a tool from an MCP server."""
    name: str
    description: str
    server_name: str
    server_url: str
    parameters: List[Dict[str, Any]] = Field(default_factory=list)
    category: str = "general"
    
    
class MCPToolResult(BaseModel):
    """Result from executing an MCP tool."""
    success: bool
    data: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    execution_time_ms: float = 0.0
    tool_name: str = ""
    server_name: str = ""


class MCPServerStatus(BaseModel):
    """Status of an MCP server connection."""
    name: str
    url: str
    connected: bool
    tools_count: int = 0
    last_check: Optional[datetime] = None
    error: Optional[str] = None


# =============================================================================
# MCP Client Connection
# =============================================================================

class MCPClientConnection:
    """
    Client connection to a single MCP server.
    
    Handles:
    - Health checking
    - Tool discovery
    - Tool execution via HTTP (simplified from full SSE)
    """
    
    def __init__(
        self,
        name: str,
        url: str,
        timeout: float = 30.0,
    ):
        self.name = name
        self.url = url.rstrip("/")
        self.timeout = timeout
        self._http_client: Optional[httpx.AsyncClient] = None
        self._connected = False
        self._tools: Dict[str, MCPToolDefinition] = {}
        self._last_check: Optional[datetime] = None
    
    async def connect(self) -> bool:
        """
        Establish connection and discover tools.
        
        Returns:
            True if connection successful
        """
        if not self._http_client:
            self._http_client = httpx.AsyncClient(timeout=self.timeout)
        
        try:
            # Health check
            response = await self._http_client.get(f"{self.url}/health")
            response.raise_for_status()
            
            # Discover tools
            response = await self._http_client.get(f"{self.url}/tools")
            response.raise_for_status()
            
            tools_data = response.json().get("tools", [])
            self._tools.clear()
            
            for tool in tools_data:
                tool_def = MCPToolDefinition(
                    name=tool["name"],
                    description=tool.get("description", ""),
                    server_name=self.name,
                    server_url=self.url,
                    parameters=tool.get("parameters", []),
                    category=tool.get("category", "general"),
                )
                self._tools[tool["name"]] = tool_def
            
            self._connected = True
            self._last_check = datetime.utcnow()
            
            logger.info(f"Connected to MCP server '{self.name}' with {len(self._tools)} tools")
            return True
            
        except Exception as e:
            logger.warning(f"Failed to connect to MCP server '{self.name}' at {self.url}: {e}")
            self._connected = False
            self._last_check = datetime.utcnow()
            return False
    
    async def disconnect(self):
        """Close the connection."""
        if self._http_client:
            await self._http_client.aclose()
            self._http_client = None
        self._connected = False
        self._tools.clear()
    
    async def call_tool(
        self,
        name: str,
        arguments: Dict[str, Any],
    ) -> MCPToolResult:
        """
        Execute a tool on the MCP server.
        
        For MCP over SSE, this would use the streaming protocol.
        For simplicity, we use direct HTTP POST to tool endpoints.
        """
        if not self._connected:
            return MCPToolResult(
                success=False,
                error=f"Server '{self.name}' not connected",
                tool_name=name,
                server_name=self.name,
            )
        
        if name not in self._tools:
            return MCPToolResult(
                success=False,
                error=f"Unknown tool '{name}' on server '{self.name}'",
                tool_name=name,
                server_name=self.name,
            )
        
        start_time = datetime.utcnow()
        
        try:
            # Call tool via POST endpoint
            # MCP servers expose tools at /tools/{name} for direct invocation
            response = await self._http_client.post(
                f"{self.url}/tools/{name}",
                json=arguments,
            )
            
            execution_time = (datetime.utcnow() - start_time).total_seconds() * 1000
            
            if response.status_code == 200:
                return MCPToolResult(
                    success=True,
                    data=response.json(),
                    execution_time_ms=execution_time,
                    tool_name=name,
                    server_name=self.name,
                )
            elif response.status_code == 404:
                # Tool endpoint not found, try SSE approach
                return await self._call_tool_sse(name, arguments, start_time)
            else:
                return MCPToolResult(
                    success=False,
                    error=f"HTTP {response.status_code}: {response.text}",
                    execution_time_ms=execution_time,
                    tool_name=name,
                    server_name=self.name,
                )
                
        except Exception as e:
            execution_time = (datetime.utcnow() - start_time).total_seconds() * 1000
            logger.error(f"Tool call failed: {name} on {self.name}: {e}")
            return MCPToolResult(
                success=False,
                error=str(e),
                execution_time_ms=execution_time,
                tool_name=name,
                server_name=self.name,
            )
    
    async def _call_tool_sse(
        self,
        name: str,
        arguments: Dict[str, Any],
        start_time: datetime,
    ) -> MCPToolResult:
        """
        Fallback: Call tool via SSE protocol.
        
        This is a simplified implementation. Full MCP SSE requires
        maintaining a streaming connection.
        """
        try:
            # For now, return an error indicating SSE is needed
            execution_time = (datetime.utcnow() - start_time).total_seconds() * 1000
            return MCPToolResult(
                success=False,
                error="SSE transport not implemented for direct tool calls",
                execution_time_ms=execution_time,
                tool_name=name,
                server_name=self.name,
            )
        except Exception as e:
            execution_time = (datetime.utcnow() - start_time).total_seconds() * 1000
            return MCPToolResult(
                success=False,
                error=str(e),
                execution_time_ms=execution_time,
                tool_name=name,
                server_name=self.name,
            )
    
    @property
    def is_connected(self) -> bool:
        return self._connected
    
    @property
    def tools(self) -> Dict[str, MCPToolDefinition]:
        return self._tools.copy()
    
    def get_status(self) -> MCPServerStatus:
        """Get connection status."""
        return MCPServerStatus(
            name=self.name,
            url=self.url,
            connected=self._connected,
            tools_count=len(self._tools),
            last_check=self._last_check,
        )


# =============================================================================
# MCP Client Manager
# =============================================================================

class MCPClientManager:
    """
    Manager for multiple MCP server connections.
    
    Provides:
    - Automatic server discovery from config
    - Tool aggregation across all servers
    - LangChain tool binding for LangGraph
    - Graceful handling of offline servers
    
    Usage:
        manager = MCPClientManager()
        await manager.initialize()
        
        # Get all tools for LangGraph
        tools = manager.get_langchain_tools()
        
        # Call a specific tool
        result = await manager.call_tool("get_ticket", {"ticket_key": "PROJ-123"})
    """
    
    def __init__(self):
        self._servers: Dict[str, MCPClientConnection] = {}
        self._tool_to_server: Dict[str, str] = {}
        self._initialized = False
    
    async def initialize(self) -> bool:
        """
        Initialize connections to all MCP servers from config.
        
        Returns:
            True if at least one server connected
        """
        # Discover servers from AgentRegistry
        agents = AgentRegistry.get_all_agents()
        
        for agent_id, agent_info in agents.items():
            # Skip non-MCP services
            if agent_id in ["analytics", "webhooks"]:
                continue
            
            url = await AgentRegistry.get_agent_url(agent_id)
            if url:
                self._servers[agent_id] = MCPClientConnection(
                    name=agent_info["name"],
                    url=url,
                )
        
        # Also add custom servers from environment
        custom_servers = os.environ.get("NEXUS_MCP_SERVERS", "")
        if custom_servers:
            for server_spec in custom_servers.split(","):
                if "=" in server_spec:
                    name, url = server_spec.split("=", 1)
                    self._servers[name.strip()] = MCPClientConnection(
                        name=name.strip(),
                        url=url.strip(),
                    )
        
        # Connect to all servers
        await self.connect_all()
        
        self._initialized = True
        return any(s.is_connected for s in self._servers.values())
    
    async def connect_all(self):
        """Connect to all registered servers."""
        tasks = []
        for name, client in self._servers.items():
            tasks.append(self._connect_and_index(name, client))
        
        await asyncio.gather(*tasks, return_exceptions=True)
    
    async def _connect_and_index(self, name: str, client: MCPClientConnection):
        """Connect to a server and index its tools."""
        try:
            connected = await client.connect()
            
            if connected:
                for tool_name in client.tools.keys():
                    self._tool_to_server[tool_name] = name
                logger.info(f"Indexed {len(client.tools)} tools from {name}")
        except Exception as e:
            logger.warning(f"Failed to connect/index {name}: {e}")
    
    async def disconnect_all(self):
        """Disconnect from all servers."""
        for client in self._servers.values():
            await client.disconnect()
        self._tool_to_server.clear()
        self._initialized = False
    
    async def refresh_connections(self):
        """Refresh all connections and rediscover tools."""
        self._tool_to_server.clear()
        await self.connect_all()
    
    def get_all_tools(self) -> List[MCPToolDefinition]:
        """Get all tools from all connected servers."""
        all_tools = []
        for client in self._servers.values():
            if client.is_connected:
                all_tools.extend(client.tools.values())
        return all_tools
    
    def get_tools_by_category(self, category: str) -> List[MCPToolDefinition]:
        """Get tools filtered by category."""
        return [t for t in self.get_all_tools() if t.category == category]
    
    async def call_tool(
        self,
        name: str,
        arguments: Dict[str, Any],
    ) -> MCPToolResult:
        """
        Call a tool by name, routing to the appropriate server.
        
        Args:
            name: Tool name
            arguments: Tool arguments
            
        Returns:
            MCPToolResult with execution result
        """
        server_name = self._tool_to_server.get(name)
        
        if not server_name:
            return MCPToolResult(
                success=False,
                error=f"Unknown tool: {name}",
                tool_name=name,
            )
        
        client = self._servers.get(server_name)
        if not client or not client.is_connected:
            return MCPToolResult(
                success=False,
                error=f"Server '{server_name}' not connected",
                tool_name=name,
                server_name=server_name,
            )
        
        return await client.call_tool(name, arguments)
    
    def get_langchain_tools(self) -> List[BaseTool]:
        """
        Convert all MCP tools to LangChain tools for use with LangGraph.
        
        Returns:
            List of LangChain StructuredTool instances
        """
        langchain_tools = []
        
        for tool_def in self.get_all_tools():
            # Create async wrapper
            async def _tool_executor(
                _tool_name: str = tool_def.name,
                **kwargs,
            ) -> str:
                result = await self.call_tool(_tool_name, kwargs)
                if result.success:
                    return json.dumps(result.data, default=str)
                else:
                    return f"Error: {result.error}"
            
            # Build args schema
            args_schema = {}
            required = []
            
            for param in tool_def.parameters:
                param_name = param.get("name", "")
                param_type = param.get("type", "string")
                is_required = param.get("required", True)
                
                if param_name:
                    if param_type == "integer":
                        args_schema[param_name] = (int, ... if is_required else None)
                    elif param_type == "number":
                        args_schema[param_name] = (float, ... if is_required else None)
                    elif param_type == "boolean":
                        args_schema[param_name] = (bool, ... if is_required else None)
                    elif param_type == "array":
                        args_schema[param_name] = (list, ... if is_required else None)
                    elif param_type == "object":
                        args_schema[param_name] = (dict, ... if is_required else None)
                    else:
                        args_schema[param_name] = (str, ... if is_required else None)
                    
                    if is_required:
                        required.append(param_name)
            
            # Create synchronous wrapper for LangChain
            def _sync_wrapper(tool_name=tool_def.name, **kwargs):
                import asyncio
                loop = asyncio.get_event_loop()
                if loop.is_running():
                    # Create a new task in the existing loop
                    import concurrent.futures
                    with concurrent.futures.ThreadPoolExecutor() as pool:
                        future = pool.submit(
                            asyncio.run,
                            self.call_tool(tool_name, kwargs)
                        )
                        result = future.result()
                else:
                    result = asyncio.run(self.call_tool(tool_name, kwargs))
                
                if result.success:
                    return json.dumps(result.data, default=str)
                else:
                    return f"Error: {result.error}"
            
            tool = StructuredTool(
                name=tool_def.name,
                description=tool_def.description,
                func=_sync_wrapper,
                coroutine=_tool_executor,
            )
            
            langchain_tools.append(tool)
        
        return langchain_tools
    
    def get_server_statuses(self) -> List[MCPServerStatus]:
        """Get status of all servers."""
        return [client.get_status() for client in self._servers.values()]
    
    @property
    def is_initialized(self) -> bool:
        return self._initialized
    
    @property
    def connected_count(self) -> int:
        return sum(1 for s in self._servers.values() if s.is_connected)
    
    @property
    def total_tools(self) -> int:
        return len(self._tool_to_server)


# =============================================================================
# Singleton Instance
# =============================================================================

_manager_instance: Optional[MCPClientManager] = None


async def get_mcp_manager() -> MCPClientManager:
    """
    Get or create the singleton MCP manager instance.
    
    Usage:
        manager = await get_mcp_manager()
        tools = manager.get_langchain_tools()
    """
    global _manager_instance
    
    if _manager_instance is None:
        _manager_instance = MCPClientManager()
        await _manager_instance.initialize()
    
    return _manager_instance


async def refresh_mcp_manager():
    """Refresh the MCP manager connections."""
    global _manager_instance
    
    if _manager_instance:
        await _manager_instance.refresh_connections()


async def close_mcp_manager():
    """Close all MCP connections."""
    global _manager_instance
    
    if _manager_instance:
        await _manager_instance.disconnect_all()
        _manager_instance = None

