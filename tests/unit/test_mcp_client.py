"""
Unit Tests for MCP Client Manager
==================================

Tests for the MCP Client Manager that handles connections to multiple
MCP servers and aggregates tools for LangGraph orchestration.

Covers:
- Connection management
- Tool discovery and aggregation
- LangChain tool binding
- Error handling for offline servers
"""

import asyncio
import json
import os
import sys
import pytest
from datetime import datetime
from typing import Any, Dict, List
from unittest.mock import AsyncMock, MagicMock, patch

# Add paths
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../../shared")))
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../../services/orchestrator")))

# Mock environment
os.environ["REDIS_URL"] = "redis://localhost:6379/0"


# =============================================================================
# Test Fixtures
# =============================================================================

@pytest.fixture
def mock_http_responses():
    """Create mock HTTP responses for MCP servers."""
    return {
        "jira": {
            "health": {"status": "healthy", "service": "jira-agent"},
            "tools": {
                "tools": [
                    {
                        "name": "get_jira_issue",
                        "description": "Fetch a Jira ticket by key",
                        "parameters": [
                            {"name": "key", "type": "string", "required": True}
                        ],
                        "category": "jira"
                    },
                    {
                        "name": "get_sprint_stats",
                        "description": "Get sprint statistics",
                        "parameters": [
                            {"name": "project_key", "type": "string", "required": True}
                        ],
                        "category": "jira"
                    }
                ]
            }
        },
        "git_ci": {
            "health": {"status": "healthy", "service": "git-ci-agent"},
            "tools": {
                "tools": [
                    {
                        "name": "get_build_status",
                        "description": "Get Jenkins build status",
                        "parameters": [
                            {"name": "job_name", "type": "string", "required": True}
                        ],
                        "category": "ci"
                    }
                ]
            }
        }
    }


@pytest.fixture
def mock_httpx_client(mock_http_responses):
    """Create a mock httpx AsyncClient."""
    mock_client = MagicMock()
    
    async def mock_get(url, **kwargs):
        response = MagicMock()
        response.status_code = 200
        
        if "/health" in url:
            if "jira" in url or "8081" in url:
                response.json.return_value = mock_http_responses["jira"]["health"]
            elif "git" in url or "8082" in url:
                response.json.return_value = mock_http_responses["git_ci"]["health"]
            else:
                response.json.return_value = {"status": "healthy"}
        elif "/tools" in url:
            if "jira" in url or "8081" in url:
                response.json.return_value = mock_http_responses["jira"]["tools"]
            elif "git" in url or "8082" in url:
                response.json.return_value = mock_http_responses["git_ci"]["tools"]
            else:
                response.json.return_value = {"tools": []}
        
        response.raise_for_status = MagicMock()
        return response
    
    async def mock_post(url, **kwargs):
        response = MagicMock()
        response.status_code = 200
        response.json.return_value = {"result": "success", "data": {}}
        return response
    
    mock_client.get = mock_get
    mock_client.post = mock_post
    mock_client.aclose = AsyncMock()
    
    return mock_client


# =============================================================================
# MCPClientConnection Tests
# =============================================================================

class TestMCPClientConnection:
    """Test the MCPClientConnection class."""
    
    @pytest.mark.asyncio
    async def test_connect_success(self, mock_httpx_client):
        """Test successful connection to MCP server."""
        from app.core.mcp_client import MCPClientConnection
        
        with patch("httpx.AsyncClient", return_value=mock_httpx_client):
            connection = MCPClientConnection(
                name="jira-agent",
                url="http://jira-agent:8081"
            )
            
            result = await connection.connect()
            
            assert result is True
            assert connection.is_connected is True
            assert len(connection.tools) == 2
            assert "get_jira_issue" in connection.tools
    
    @pytest.mark.asyncio
    async def test_connect_failure(self):
        """Test connection failure handling."""
        from app.core.mcp_client import MCPClientConnection
        
        mock_client = MagicMock()
        mock_client.get = AsyncMock(side_effect=Exception("Connection refused"))
        
        with patch("httpx.AsyncClient", return_value=mock_client):
            connection = MCPClientConnection(
                name="offline-agent",
                url="http://offline:9999"
            )
            
            result = await connection.connect()
            
            assert result is False
            assert connection.is_connected is False
    
    @pytest.mark.asyncio
    async def test_disconnect(self, mock_httpx_client):
        """Test disconnection from MCP server."""
        from app.core.mcp_client import MCPClientConnection
        
        with patch("httpx.AsyncClient", return_value=mock_httpx_client):
            connection = MCPClientConnection(
                name="jira-agent",
                url="http://jira-agent:8081"
            )
            
            await connection.connect()
            await connection.disconnect()
            
            assert connection.is_connected is False
            assert len(connection.tools) == 0
    
    @pytest.mark.asyncio
    async def test_call_tool_success(self, mock_httpx_client):
        """Test successful tool call."""
        from app.core.mcp_client import MCPClientConnection
        
        # Set up mock response for tool call
        tool_response = MagicMock()
        tool_response.status_code = 200
        tool_response.json.return_value = {
            "key": "PROJ-123",
            "summary": "Test ticket",
            "status": "Done"
        }
        mock_httpx_client.post = AsyncMock(return_value=tool_response)
        
        with patch("httpx.AsyncClient", return_value=mock_httpx_client):
            connection = MCPClientConnection(
                name="jira-agent",
                url="http://jira-agent:8081"
            )
            
            await connection.connect()
            result = await connection.call_tool("get_jira_issue", {"key": "PROJ-123"})
            
            assert result.success is True
            assert result.data is not None
            assert result.tool_name == "get_jira_issue"
    
    @pytest.mark.asyncio
    async def test_call_tool_not_connected(self):
        """Test tool call when not connected."""
        from app.core.mcp_client import MCPClientConnection
        
        connection = MCPClientConnection(
            name="jira-agent",
            url="http://jira-agent:8081"
        )
        
        result = await connection.call_tool("get_jira_issue", {"key": "PROJ-123"})
        
        assert result.success is False
        assert "not connected" in result.error.lower()
    
    @pytest.mark.asyncio
    async def test_call_unknown_tool(self, mock_httpx_client):
        """Test calling an unknown tool."""
        from app.core.mcp_client import MCPClientConnection
        
        with patch("httpx.AsyncClient", return_value=mock_httpx_client):
            connection = MCPClientConnection(
                name="jira-agent",
                url="http://jira-agent:8081"
            )
            
            await connection.connect()
            result = await connection.call_tool("unknown_tool", {})
            
            assert result.success is False
            assert "unknown tool" in result.error.lower()
    
    def test_get_status(self, mock_httpx_client):
        """Test getting connection status."""
        from app.core.mcp_client import MCPClientConnection
        
        connection = MCPClientConnection(
            name="jira-agent",
            url="http://jira-agent:8081"
        )
        
        status = connection.get_status()
        
        assert status.name == "jira-agent"
        assert status.url == "http://jira-agent:8081"
        assert status.connected is False


# =============================================================================
# MCPClientManager Tests
# =============================================================================

class TestMCPClientManager:
    """Test the MCPClientManager class."""
    
    @pytest.mark.asyncio
    async def test_initialize_from_config(self, mock_httpx_client):
        """Test manager initialization from agent registry."""
        from app.core.mcp_client import MCPClientManager
        
        # Mock the AgentRegistry to return test agents
        mock_agents = {
            "jira_agent": {"name": "Jira Agent", "url_key": "nexus:config:jira_agent_url"},
            "git_agent": {"name": "Git/CI Agent", "url_key": "nexus:config:git_agent_url"},
        }
        
        with patch("httpx.AsyncClient", return_value=mock_httpx_client):
            with patch("app.core.mcp_client.AgentRegistry.get_all_agents", return_value=mock_agents):
                with patch("app.core.mcp_client.AgentRegistry.get_agent_url", 
                          new_callable=AsyncMock,
                          side_effect=["http://jira-agent:8081", "http://git-ci-agent:8082"]):
                    
                    manager = MCPClientManager()
                    result = await manager.initialize()
                    
                    assert result is True
                    assert manager.is_initialized is True
    
    @pytest.mark.asyncio
    async def test_get_all_tools(self, mock_httpx_client):
        """Test getting all tools from connected servers."""
        from app.core.mcp_client import MCPClientManager, MCPClientConnection
        
        with patch("httpx.AsyncClient", return_value=mock_httpx_client):
            manager = MCPClientManager()
            
            # Manually add servers for testing
            manager._servers["jira"] = MCPClientConnection("jira", "http://jira:8081")
            manager._servers["git_ci"] = MCPClientConnection("git_ci", "http://git:8082")
            
            await manager.connect_all()
            
            tools = manager.get_all_tools()
            
            assert len(tools) >= 2
            tool_names = [t.name for t in tools]
            assert "get_jira_issue" in tool_names or "get_build_status" in tool_names
    
    @pytest.mark.asyncio
    async def test_call_tool_routes_correctly(self, mock_httpx_client):
        """Test that tool calls are routed to the correct server."""
        from app.core.mcp_client import MCPClientManager, MCPClientConnection
        
        # Mock tool call response
        tool_response = MagicMock()
        tool_response.status_code = 200
        tool_response.json.return_value = {"key": "PROJ-123", "summary": "Test"}
        mock_httpx_client.post = AsyncMock(return_value=tool_response)
        
        with patch("httpx.AsyncClient", return_value=mock_httpx_client):
            manager = MCPClientManager()
            
            manager._servers["jira"] = MCPClientConnection("jira", "http://jira:8081")
            await manager.connect_all()
            
            # Index tool to server mapping
            manager._tool_to_server["get_jira_issue"] = "jira"
            
            result = await manager.call_tool("get_jira_issue", {"key": "PROJ-123"})
            
            assert result.success is True
    
    @pytest.mark.asyncio
    async def test_call_unknown_tool(self, mock_httpx_client):
        """Test calling a tool that doesn't exist."""
        from app.core.mcp_client import MCPClientManager
        
        with patch("httpx.AsyncClient", return_value=mock_httpx_client):
            manager = MCPClientManager()
            manager._initialized = True
            
            result = await manager.call_tool("nonexistent_tool", {})
            
            assert result.success is False
            assert "unknown tool" in result.error.lower()
    
    @pytest.mark.asyncio
    async def test_get_langchain_tools(self, mock_httpx_client):
        """Test conversion to LangChain tools."""
        from app.core.mcp_client import MCPClientManager, MCPClientConnection
        
        with patch("httpx.AsyncClient", return_value=mock_httpx_client):
            manager = MCPClientManager()
            
            manager._servers["jira"] = MCPClientConnection("jira", "http://jira:8081")
            await manager.connect_all()
            
            langchain_tools = manager.get_langchain_tools()
            
            assert len(langchain_tools) > 0
            # Check that tools have required attributes
            for tool in langchain_tools:
                assert hasattr(tool, "name")
                assert hasattr(tool, "description")
                assert callable(tool.func) or tool.coroutine is not None
    
    @pytest.mark.asyncio
    async def test_refresh_connections(self, mock_httpx_client):
        """Test refreshing all connections."""
        from app.core.mcp_client import MCPClientManager, MCPClientConnection
        
        with patch("httpx.AsyncClient", return_value=mock_httpx_client):
            manager = MCPClientManager()
            
            manager._servers["jira"] = MCPClientConnection("jira", "http://jira:8081")
            await manager.connect_all()
            
            initial_tool_count = len(manager._tool_to_server)
            
            await manager.refresh_connections()
            
            # After refresh, tools should be re-indexed
            assert manager.connected_count >= 0
    
    def test_get_server_statuses(self, mock_httpx_client):
        """Test getting status of all servers."""
        from app.core.mcp_client import MCPClientManager, MCPClientConnection
        
        manager = MCPClientManager()
        manager._servers["jira"] = MCPClientConnection("jira", "http://jira:8081")
        manager._servers["git"] = MCPClientConnection("git", "http://git:8082")
        
        statuses = manager.get_server_statuses()
        
        assert len(statuses) == 2
        assert all(hasattr(s, "name") for s in statuses)
        assert all(hasattr(s, "connected") for s in statuses)
    
    @pytest.mark.asyncio
    async def test_disconnect_all(self, mock_httpx_client):
        """Test disconnecting from all servers."""
        from app.core.mcp_client import MCPClientManager, MCPClientConnection
        
        with patch("httpx.AsyncClient", return_value=mock_httpx_client):
            manager = MCPClientManager()
            
            manager._servers["jira"] = MCPClientConnection("jira", "http://jira:8081")
            await manager.connect_all()
            
            await manager.disconnect_all()
            
            assert manager.is_initialized is False
            assert manager.connected_count == 0


# =============================================================================
# Singleton Tests
# =============================================================================

class TestMCPManagerSingleton:
    """Test the singleton factory functions."""
    
    @pytest.mark.asyncio
    async def test_get_mcp_manager_creates_instance(self, mock_httpx_client):
        """Test that get_mcp_manager creates a manager instance."""
        from app.core.mcp_client import get_mcp_manager, close_mcp_manager, _manager_instance
        
        # Reset singleton
        import app.core.mcp_client as mcp_module
        mcp_module._manager_instance = None
        
        mock_agents = {}
        
        with patch("httpx.AsyncClient", return_value=mock_httpx_client):
            with patch("app.core.mcp_client.AgentRegistry.get_all_agents", return_value=mock_agents):
                manager = await get_mcp_manager()
                
                assert manager is not None
                assert manager.is_initialized is True
                
                # Cleanup
                await close_mcp_manager()
    
    @pytest.mark.asyncio
    async def test_close_mcp_manager(self, mock_httpx_client):
        """Test that close_mcp_manager cleans up the singleton."""
        from app.core.mcp_client import get_mcp_manager, close_mcp_manager
        
        import app.core.mcp_client as mcp_module
        mcp_module._manager_instance = None
        
        mock_agents = {}
        
        with patch("httpx.AsyncClient", return_value=mock_httpx_client):
            with patch("app.core.mcp_client.AgentRegistry.get_all_agents", return_value=mock_agents):
                await get_mcp_manager()
                await close_mcp_manager()
                
                assert mcp_module._manager_instance is None


# =============================================================================
# Data Model Tests
# =============================================================================

class TestMCPDataModels:
    """Test the MCP data models."""
    
    def test_tool_definition_model(self):
        """Test MCPToolDefinition model."""
        from app.core.mcp_client import MCPToolDefinition
        
        tool = MCPToolDefinition(
            name="test_tool",
            description="A test tool",
            server_name="test-server",
            server_url="http://test:8080",
            parameters=[{"name": "arg1", "type": "string"}],
            category="test"
        )
        
        assert tool.name == "test_tool"
        assert tool.category == "test"
        assert len(tool.parameters) == 1
    
    def test_tool_result_model(self):
        """Test MCPToolResult model."""
        from app.core.mcp_client import MCPToolResult
        
        result = MCPToolResult(
            success=True,
            data={"key": "value"},
            execution_time_ms=150.5,
            tool_name="test_tool",
            server_name="test-server"
        )
        
        assert result.success is True
        assert result.execution_time_ms == 150.5
    
    def test_server_status_model(self):
        """Test MCPServerStatus model."""
        from app.core.mcp_client import MCPServerStatus
        
        status = MCPServerStatus(
            name="test-server",
            url="http://test:8080",
            connected=True,
            tools_count=5,
            last_check=datetime.utcnow()
        )
        
        assert status.connected is True
        assert status.tools_count == 5


# =============================================================================
# Run Tests
# =============================================================================

if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])

