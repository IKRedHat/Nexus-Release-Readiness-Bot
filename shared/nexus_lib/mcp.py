"""
Nexus MCP (Model Context Protocol) Utilities
============================================

Shared utilities for creating SSE-based MCP servers across all Nexus agents.
This module provides a standardized way to expose tools via MCP, replacing
the previous FastAPI REST endpoints.

Features:
- SSE transport using starlette
- Standard tool registration decorators
- Error handling and logging
- Graceful shutdown support
- Health check integration

Usage:
    from nexus_lib.mcp import NexusMCPServer, create_mcp_app

    server = NexusMCPServer("jira-agent", "Jira operations for release management")
    
    @server.tool()
    async def get_ticket(ticket_key: str) -> dict:
        '''Get a Jira ticket by key'''
        return await jira_client.get_issue(ticket_key)
    
    app = create_mcp_app(server)

Author: Nexus Team
Version: 3.0.0
"""

import asyncio
import json
import logging
import os
import signal
import sys
from contextlib import asynccontextmanager
from datetime import datetime
from typing import Any, Callable, Dict, List, Optional, Type, Union
from functools import wraps
import traceback

from pydantic import BaseModel, Field
from starlette.applications import Starlette
from starlette.responses import JSONResponse, Response
from starlette.routing import Route
from starlette.requests import Request
from sse_starlette.sse import EventSourceResponse

try:
    from mcp.server import Server
    from mcp.server.sse import SseServerTransport
    from mcp.types import (
        Tool,
        TextContent,
        CallToolResult,
        ListToolsResult,
        ErrorData,
        INTERNAL_ERROR,
        INVALID_PARAMS,
    )
    MCP_AVAILABLE = True
except ImportError:
    MCP_AVAILABLE = False
    # Define minimal stubs for type hints when MCP is not installed
    class Server:
        pass
    class Tool:
        pass

logger = logging.getLogger("nexus.mcp")


# =============================================================================
# MCP Tool Definition Models
# =============================================================================

class ToolParameter(BaseModel):
    """Parameter definition for an MCP tool."""
    name: str
    type: str = "string"
    description: str = ""
    required: bool = True
    default: Optional[Any] = None
    enum: Optional[List[Any]] = None


class ToolDefinition(BaseModel):
    """Complete tool definition for registration."""
    name: str
    description: str
    parameters: List[ToolParameter] = Field(default_factory=list)
    handler: Optional[Callable] = Field(default=None, exclude=True)
    category: str = "general"
    
    class Config:
        arbitrary_types_allowed = True


class MCPToolResult(BaseModel):
    """Standardized result from an MCP tool execution."""
    success: bool
    data: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    execution_time_ms: float = 0.0
    tool_name: str = ""


# =============================================================================
# MCP Server Implementation
# =============================================================================

class NexusMCPServer:
    """
    Nexus MCP Server wrapper for creating tool-based agents.
    
    This class provides a simple decorator-based API for registering tools
    that will be exposed via MCP over SSE transport.
    """
    
    def __init__(
        self,
        name: str,
        description: str,
        version: str = "3.0.0",
        port: int = 8000,
    ):
        """
        Initialize the MCP server.
        
        Args:
            name: Server name (e.g., "jira-agent")
            description: Human-readable description
            version: Server version
            port: Port to listen on
        """
        self.name = name
        self.description = description
        self.version = version
        self.port = port
        self.tools: Dict[str, ToolDefinition] = {}
        self._server: Optional[Server] = None
        self._transport: Optional[SseServerTransport] = None
        self._running = False
        self._startup_callbacks: List[Callable] = []
        self._shutdown_callbacks: List[Callable] = []
        
        if MCP_AVAILABLE:
            self._server = Server(name)
            self._setup_handlers()
        else:
            logger.warning(f"MCP SDK not available - {name} will run in fallback mode")
    
    def _setup_handlers(self):
        """Set up MCP protocol handlers."""
        if not self._server:
            return
        
        @self._server.list_tools()
        async def list_tools() -> ListToolsResult:
            """Return list of available tools."""
            mcp_tools = []
            for tool_def in self.tools.values():
                # Build JSON schema for parameters
                properties = {}
                required = []
                
                for param in tool_def.parameters:
                    prop = {"type": param.type, "description": param.description}
                    if param.enum:
                        prop["enum"] = param.enum
                    if param.default is not None:
                        prop["default"] = param.default
                    properties[param.name] = prop
                    
                    if param.required:
                        required.append(param.name)
                
                input_schema = {
                    "type": "object",
                    "properties": properties,
                    "required": required,
                }
                
                mcp_tools.append(Tool(
                    name=tool_def.name,
                    description=tool_def.description,
                    inputSchema=input_schema,
                ))
            
            return ListToolsResult(tools=mcp_tools)
        
        @self._server.call_tool()
        async def call_tool(name: str, arguments: Dict[str, Any]) -> CallToolResult:
            """Execute a tool and return the result."""
            start_time = datetime.now()
            
            if name not in self.tools:
                return CallToolResult(
                    content=[TextContent(type="text", text=f"Unknown tool: {name}")],
                    isError=True,
                )
            
            tool_def = self.tools[name]
            
            try:
                # Execute the tool handler
                if asyncio.iscoroutinefunction(tool_def.handler):
                    result = await tool_def.handler(**arguments)
                else:
                    result = tool_def.handler(**arguments)
                
                execution_time = (datetime.now() - start_time).total_seconds() * 1000
                
                # Format result
                if isinstance(result, BaseModel):
                    result_text = result.model_dump_json()
                elif isinstance(result, dict):
                    result_text = json.dumps(result, default=str)
                else:
                    result_text = str(result)
                
                logger.info(f"Tool {name} executed in {execution_time:.2f}ms")
                
                return CallToolResult(
                    content=[TextContent(type="text", text=result_text)],
                    isError=False,
                )
                
            except Exception as e:
                logger.exception(f"Tool {name} failed: {e}")
                return CallToolResult(
                    content=[TextContent(type="text", text=f"Error: {str(e)}")],
                    isError=True,
                )
    
    def tool(
        self,
        name: Optional[str] = None,
        description: Optional[str] = None,
        category: str = "general",
    ):
        """
        Decorator to register a function as an MCP tool.
        
        Args:
            name: Tool name (defaults to function name)
            description: Tool description (defaults to docstring)
            category: Tool category for organization
            
        Usage:
            @server.tool()
            async def get_ticket(ticket_key: str) -> dict:
                '''Get a Jira ticket by key'''
                return await jira_client.get_issue(ticket_key)
        """
        def decorator(func: Callable) -> Callable:
            tool_name = name or func.__name__
            tool_description = description or func.__doc__ or f"Execute {tool_name}"
            
            # Extract parameters from function signature
            import inspect
            sig = inspect.signature(func)
            parameters = []
            
            for param_name, param in sig.parameters.items():
                if param_name in ('self', 'cls'):
                    continue
                
                # Determine parameter type
                param_type = "string"
                if param.annotation != inspect.Parameter.empty:
                    if param.annotation == int:
                        param_type = "integer"
                    elif param.annotation == float:
                        param_type = "number"
                    elif param.annotation == bool:
                        param_type = "boolean"
                    elif param.annotation == list or param.annotation == List:
                        param_type = "array"
                    elif param.annotation == dict or param.annotation == Dict:
                        param_type = "object"
                
                # Check if required
                required = param.default == inspect.Parameter.empty
                default = None if param.default == inspect.Parameter.empty else param.default
                
                parameters.append(ToolParameter(
                    name=param_name,
                    type=param_type,
                    description=f"Parameter: {param_name}",
                    required=required,
                    default=default,
                ))
            
            # Register the tool
            self.tools[tool_name] = ToolDefinition(
                name=tool_name,
                description=tool_description,
                parameters=parameters,
                handler=func,
                category=category,
            )
            
            logger.info(f"Registered tool: {tool_name} ({len(parameters)} params)")
            
            return func
        
        return decorator
    
    def on_startup(self, callback: Callable):
        """Register a startup callback."""
        self._startup_callbacks.append(callback)
        return callback
    
    def on_shutdown(self, callback: Callable):
        """Register a shutdown callback."""
        self._shutdown_callbacks.append(callback)
        return callback
    
    async def handle_sse(self, request: Request):
        """Handle SSE connection for MCP transport."""
        if not MCP_AVAILABLE:
            return JSONResponse(
                {"error": "MCP SDK not available"},
                status_code=503
            )
        
        async def event_generator():
            """Generate SSE events."""
            self._transport = SseServerTransport("/messages")
            
            async with self._transport.connect_sse(
                request.scope,
                request.receive,
            ) as (read_stream, write_stream):
                await self._server.run(
                    read_stream,
                    write_stream,
                    self._server.create_initialization_options(),
                )
        
        return EventSourceResponse(event_generator())
    
    async def handle_messages(self, request: Request):
        """Handle incoming MCP messages."""
        if not self._transport:
            return JSONResponse(
                {"error": "No active SSE connection"},
                status_code=400
            )
        
        body = await request.body()
        await self._transport.handle_post_message(
            request.scope,
            request.receive,
            body,
        )
        return Response(status_code=202)
    
    def get_health(self) -> Dict[str, Any]:
        """Get server health status."""
        return {
            "status": "healthy",
            "service": self.name,
            "version": self.version,
            "mcp_enabled": MCP_AVAILABLE,
            "tools_count": len(self.tools),
            "tools": list(self.tools.keys()),
        }


# =============================================================================
# Starlette App Factory
# =============================================================================

def create_mcp_app(
    server: NexusMCPServer,
    enable_health: bool = True,
    enable_metrics: bool = True,
) -> Starlette:
    """
    Create a Starlette application with MCP SSE endpoints.
    
    Args:
        server: NexusMCPServer instance
        enable_health: Include /health endpoint
        enable_metrics: Include /metrics endpoint
        
    Returns:
        Configured Starlette application
    """
    
    @asynccontextmanager
    async def lifespan(app: Starlette):
        """Application lifespan manager."""
        logger.info(f"Starting MCP server: {server.name}")
        
        # Run startup callbacks
        for callback in server._startup_callbacks:
            if asyncio.iscoroutinefunction(callback):
                await callback()
            else:
                callback()
        
        server._running = True
        logger.info(f"MCP server {server.name} ready with {len(server.tools)} tools")
        
        yield
        
        # Run shutdown callbacks
        logger.info(f"Shutting down MCP server: {server.name}")
        server._running = False
        
        for callback in server._shutdown_callbacks:
            if asyncio.iscoroutinefunction(callback):
                await callback()
            else:
                callback()
        
        logger.info(f"MCP server {server.name} shutdown complete")
    
    # Build routes
    routes = [
        Route("/sse", server.handle_sse, methods=["GET"]),
        Route("/messages", server.handle_messages, methods=["POST"]),
    ]
    
    if enable_health:
        async def health(request: Request):
            return JSONResponse(server.get_health())
        routes.append(Route("/health", health, methods=["GET"]))
    
    if enable_metrics:
        async def metrics(request: Request):
            # Basic metrics - can be extended with prometheus_client
            return Response(
                content=f"# HELP nexus_mcp_tools_total Number of registered MCP tools\n"
                        f"# TYPE nexus_mcp_tools_total gauge\n"
                        f"nexus_mcp_tools_total{{server=\"{server.name}\"}} {len(server.tools)}\n",
                media_type="text/plain",
            )
        routes.append(Route("/metrics", metrics, methods=["GET"]))
    
    # Tool listing endpoint (convenience for debugging)
    async def list_tools(request: Request):
        tools = []
        for tool_def in server.tools.values():
            tools.append({
                "name": tool_def.name,
                "description": tool_def.description,
                "category": tool_def.category,
                "parameters": [p.model_dump() for p in tool_def.parameters],
            })
        return JSONResponse({"tools": tools})
    
    routes.append(Route("/tools", list_tools, methods=["GET"]))
    
    return Starlette(
        routes=routes,
        lifespan=lifespan,
    )


# =============================================================================
# MCP Client Utilities
# =============================================================================

class MCPClientConnection:
    """
    Client connection to an MCP server over SSE.
    
    Usage:
        async with MCPClientConnection("http://jira-agent:8081") as client:
            tools = await client.list_tools()
            result = await client.call_tool("get_ticket", {"ticket_key": "PROJ-123"})
    """
    
    def __init__(
        self,
        url: str,
        name: Optional[str] = None,
        timeout: float = 30.0,
    ):
        """
        Initialize MCP client connection.
        
        Args:
            url: Base URL of the MCP server
            name: Optional name for this connection
            timeout: Request timeout in seconds
        """
        self.url = url.rstrip("/")
        self.name = name or url
        self.timeout = timeout
        self._connected = False
        self._tools: Dict[str, Tool] = {}
        self._http_client = None
    
    async def __aenter__(self):
        await self.connect()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.disconnect()
    
    async def connect(self):
        """Establish connection to the MCP server."""
        import httpx
        
        self._http_client = httpx.AsyncClient(timeout=self.timeout)
        
        try:
            # Verify server is available
            response = await self._http_client.get(f"{self.url}/health")
            response.raise_for_status()
            
            # Get available tools
            response = await self._http_client.get(f"{self.url}/tools")
            response.raise_for_status()
            
            tools_data = response.json().get("tools", [])
            for tool in tools_data:
                self._tools[tool["name"]] = tool
            
            self._connected = True
            logger.info(f"Connected to MCP server {self.name} with {len(self._tools)} tools")
            
        except Exception as e:
            logger.warning(f"Failed to connect to MCP server {self.name}: {e}")
            self._connected = False
    
    async def disconnect(self):
        """Close the connection."""
        if self._http_client:
            await self._http_client.aclose()
            self._http_client = None
        self._connected = False
    
    @property
    def is_connected(self) -> bool:
        return self._connected
    
    async def list_tools(self) -> List[Dict[str, Any]]:
        """Get list of available tools."""
        return list(self._tools.values())
    
    async def call_tool(
        self,
        name: str,
        arguments: Dict[str, Any],
    ) -> MCPToolResult:
        """
        Call a tool on the MCP server.
        
        Args:
            name: Tool name
            arguments: Tool arguments
            
        Returns:
            MCPToolResult with execution result
        """
        if not self._connected:
            return MCPToolResult(
                success=False,
                error="Not connected to MCP server",
                tool_name=name,
            )
        
        if name not in self._tools:
            return MCPToolResult(
                success=False,
                error=f"Unknown tool: {name}",
                tool_name=name,
            )
        
        start_time = datetime.now()
        
        try:
            # For SSE-based MCP, we need to establish a streaming connection
            # For simplicity, we'll use a direct POST to a tool endpoint
            # This is a simplified version - full MCP requires SSE streaming
            
            response = await self._http_client.post(
                f"{self.url}/tools/{name}",
                json=arguments,
            )
            
            execution_time = (datetime.now() - start_time).total_seconds() * 1000
            
            if response.status_code == 200:
                return MCPToolResult(
                    success=True,
                    data=response.json(),
                    execution_time_ms=execution_time,
                    tool_name=name,
                )
            else:
                return MCPToolResult(
                    success=False,
                    error=f"HTTP {response.status_code}: {response.text}",
                    execution_time_ms=execution_time,
                    tool_name=name,
                )
                
        except Exception as e:
            execution_time = (datetime.now() - start_time).total_seconds() * 1000
            return MCPToolResult(
                success=False,
                error=str(e),
                execution_time_ms=execution_time,
                tool_name=name,
            )


class MCPClientManager:
    """
    Manager for multiple MCP client connections.
    
    Aggregates tools from multiple MCP servers and provides a unified interface.
    
    Usage:
        manager = MCPClientManager()
        manager.add_server("jira", "http://jira-agent:8081")
        manager.add_server("github", "http://git-ci-agent:8082")
        
        async with manager:
            all_tools = await manager.get_all_tools()
            result = await manager.call_tool("get_ticket", {"ticket_key": "PROJ-123"})
    """
    
    def __init__(self):
        self._servers: Dict[str, MCPClientConnection] = {}
        self._tool_to_server: Dict[str, str] = {}
        self._connected = False
    
    def add_server(
        self,
        name: str,
        url: str,
        timeout: float = 30.0,
    ):
        """Add an MCP server to the manager."""
        self._servers[name] = MCPClientConnection(url, name, timeout)
    
    async def __aenter__(self):
        await self.connect_all()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.disconnect_all()
    
    async def connect_all(self):
        """Connect to all registered MCP servers."""
        tasks = []
        for name, client in self._servers.items():
            tasks.append(self._connect_server(name, client))
        
        await asyncio.gather(*tasks, return_exceptions=True)
        self._connected = True
    
    async def _connect_server(self, name: str, client: MCPClientConnection):
        """Connect to a single server and index its tools."""
        try:
            await client.connect()
            if client.is_connected:
                for tool_name in client._tools.keys():
                    self._tool_to_server[tool_name] = name
        except Exception as e:
            logger.warning(f"Failed to connect to server {name}: {e}")
    
    async def disconnect_all(self):
        """Disconnect from all servers."""
        for client in self._servers.values():
            await client.disconnect()
        self._connected = False
    
    async def get_all_tools(self) -> List[Dict[str, Any]]:
        """Get all tools from all connected servers."""
        all_tools = []
        for name, client in self._servers.items():
            if client.is_connected:
                tools = await client.list_tools()
                for tool in tools:
                    tool["server"] = name
                    all_tools.append(tool)
        return all_tools
    
    async def call_tool(
        self,
        name: str,
        arguments: Dict[str, Any],
    ) -> MCPToolResult:
        """Call a tool, routing to the appropriate server."""
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
                error=f"Server {server_name} not connected",
                tool_name=name,
            )
        
        return await client.call_tool(name, arguments)
    
    def get_langchain_tools(self) -> List:
        """
        Convert MCP tools to LangChain tool format.
        
        Returns:
            List of LangChain-compatible tools
        """
        from langchain_core.tools import StructuredTool
        
        langchain_tools = []
        
        for tool_name, server_name in self._tool_to_server.items():
            client = self._servers.get(server_name)
            if not client or not client.is_connected:
                continue
            
            tool_def = client._tools.get(tool_name)
            if not tool_def:
                continue
            
            # Create async wrapper for the tool
            async def tool_func(
                _name=tool_name,
                **kwargs,
            ) -> str:
                result = await self.call_tool(_name, kwargs)
                if result.success:
                    return json.dumps(result.data, default=str)
                else:
                    return f"Error: {result.error}"
            
            # Build args schema from tool parameters
            args_schema = {}
            for param in tool_def.get("parameters", []):
                args_schema[param["name"]] = (
                    str if param["type"] == "string" else
                    int if param["type"] == "integer" else
                    float if param["type"] == "number" else
                    bool if param["type"] == "boolean" else
                    Any
                )
            
            langchain_tools.append(StructuredTool(
                name=tool_name,
                description=tool_def.get("description", ""),
                func=lambda **kwargs: asyncio.run(tool_func(**kwargs)),
                coroutine=tool_func,
                args_schema=args_schema if args_schema else None,
            ))
        
        return langchain_tools


# =============================================================================
# Convenience Exports
# =============================================================================

__all__ = [
    "NexusMCPServer",
    "create_mcp_app",
    "MCPClientConnection",
    "MCPClientManager",
    "ToolDefinition",
    "ToolParameter",
    "MCPToolResult",
    "MCP_AVAILABLE",
]

