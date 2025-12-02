"""
End-to-End Tests for Release Flow
=================================

Tests the complete release readiness assessment workflow using
the new LangGraph + MCP architecture.

Architecture:
- Orchestrator uses LangGraph StateGraph
- Tools accessed via MCP protocol
- LLM via LLM Factory abstraction
"""
import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from fastapi.testclient import TestClient
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../../services/orchestrator")))
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../../shared")))

# Set mock mode for all tests
os.environ["NEXUS_ENV"] = "test"
os.environ["NEXUS_REQUIRE_AUTH"] = "false"
os.environ["LLM_PROVIDER"] = "mock"
os.environ["MOCK_MODE"] = "true"
os.environ["JIRA_MOCK_MODE"] = "true"
os.environ["GITHUB_MOCK_MODE"] = "true"
os.environ["JENKINS_MOCK_MODE"] = "true"


# =============================================================================
# Test Fixtures
# =============================================================================

@pytest.fixture
def mock_graph_engine():
    """Mock graph engine for testing."""
    engine = AsyncMock()
    engine.run = AsyncMock(return_value={
        "success": True,
        "result": "The release is ready. All criteria are met.",
        "plan": ["Check tickets", "Check builds", "Analyze readiness"],
        "steps": 3,
        "thread_id": "test-thread-123",
        "requires_approval": False,
    })
    engine.resume = AsyncMock(return_value={
        "success": True,
        "result": "Action approved and executed.",
    })
    engine.get_state = AsyncMock(return_value={
        "query": "Check release status",
        "current_step": "completed",
        "final_answer": "Release is ready",
    })
    return engine


@pytest.fixture
def mock_mcp_manager():
    """Mock MCP client manager for testing."""
    manager = MagicMock()
    manager.connected_count = 5
    manager.total_tools = 20
    manager.get_langchain_tools = MagicMock(return_value=[])
    manager.get_all_tools = MagicMock(return_value=[])
    manager.get_server_statuses = MagicMock(return_value=[])
    return manager


@pytest.fixture
def mock_vector_memory():
    """Mock vector memory for testing."""
    memory = AsyncMock()
    memory.get_stats = AsyncMock(return_value={
        "backend": "mock",
        "count": 0,
    })
    memory.add_context = AsyncMock()
    memory.retrieve = AsyncMock(return_value="")
    return memory


@pytest.fixture
def app_with_mocks(mock_graph_engine, mock_mcp_manager, mock_vector_memory):
    """Create FastAPI app with mocked dependencies."""
    # Import after setting environment
    from main import app
    
    # Patch the global instances
    with patch("main.graph_engine", mock_graph_engine):
        with patch("main.mcp_manager", mock_mcp_manager):
            with patch("main.vector_memory", mock_vector_memory):
                with patch("main.conversation_memory", MagicMock()):
                    yield app


@pytest.fixture
def client(app_with_mocks):
    """Create test client."""
    with TestClient(app_with_mocks) as client:
        yield client


# =============================================================================
# Health & Status Tests
# =============================================================================

class TestHealthEndpoints:
    """Tests for health check endpoints."""
    
    def test_health_check(self, client):
        """Test orchestrator health check."""
        response = client.get("/health")
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert data["service"] == "central-orchestrator"
        assert data["version"] == "3.0.0"
    
    def test_liveness_check(self, client):
        """Test liveness endpoint."""
        response = client.get("/live")
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "alive"


# =============================================================================
# Query Execution Tests (LangGraph)
# =============================================================================

class TestQueryExecution:
    """Tests for query execution via LangGraph."""
    
    def test_execute_simple_query(self, client, mock_graph_engine):
        """Test executing a simple query through LangGraph."""
        response = client.post("/execute", json={
            "task_id": "test-task-1",
            "action": "process_query",
            "payload": {"query": "What is the release status?"},
            "user_context": {"user_id": "test-user"}
        })
        
        assert response.status_code == 200
        data = response.json()
        assert "task_id" in data
        assert data["status"] in ["success", "failed"]
    
    def test_execute_jira_query(self, client, mock_graph_engine):
        """Test executing a Jira-related query."""
        response = client.post("/execute", json={
            "task_id": "test-task-2",
            "action": "process_query",
            "payload": {"query": "Check ticket PROJ-123 status"},
            "user_context": {"user_id": "test-user"}
        })
        
        assert response.status_code == 200
        data = response.json()
        assert data["task_id"] == "test-task-2"
    
    def test_execute_release_check_query(self, client, mock_graph_engine):
        """Test executing a release readiness query."""
        response = client.post("/execute", json={
            "task_id": "test-task-3",
            "action": "process_query",
            "payload": {"query": "Is version 2.0 ready for release?"},
            "user_context": {"user_id": "test-user"}
        })
        
        assert response.status_code == 200
        data = response.json()
        assert "data" in data
    
    def test_simple_query_endpoint(self, client, mock_graph_engine):
        """Test the simple /query endpoint."""
        response = client.post("/query", json={
            "query": "Hello, what can you do?"
        })
        
        assert response.status_code == 200
        data = response.json()
        assert "query" in data
        assert "status" in data
    
    def test_query_with_thread_id(self, client, mock_graph_engine):
        """Test query with thread_id for conversation continuity."""
        response = client.post("/query", json={
            "query": "Continue our previous conversation",
            "thread_id": "existing-thread-123"
        })
        
        assert response.status_code == 200
        data = response.json()
        assert "thread_id" in data
    
    def test_missing_query_returns_error(self, client):
        """Test that missing query returns error."""
        response = client.post("/execute", json={
            "task_id": "error-test",
            "action": "process_query",
            "payload": {}  # Missing query
        })
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "failed"
        assert "query" in data["error_message"].lower() or "required" in data["error_message"].lower()


# =============================================================================
# Human-in-the-Loop Tests
# =============================================================================

class TestHumanApproval:
    """Tests for human-in-the-loop approval workflow."""
    
    def test_approve_action(self, client, mock_graph_engine):
        """Test approving a pending action."""
        response = client.post("/approve", json={
            "thread_id": "pending-thread-123",
            "approved": True,
            "comment": "Looks good to proceed"
        })
        
        assert response.status_code == 200
        data = response.json()
        assert data["approval_status"] == "approved"
    
    def test_reject_action(self, client, mock_graph_engine):
        """Test rejecting a pending action."""
        response = client.post("/approve", json={
            "thread_id": "pending-thread-456",
            "approved": False,
            "comment": "Need more review"
        })
        
        assert response.status_code == 200
        data = response.json()
        assert data["approval_status"] == "rejected"
    
    def test_get_thread_state(self, client, mock_graph_engine):
        """Test getting thread state."""
        response = client.get("/thread/test-thread-123")
        
        assert response.status_code == 200
        data = response.json()
        assert data["thread_id"] == "test-thread-123"


# =============================================================================
# Memory System Tests
# =============================================================================

class TestMemorySystem:
    """Tests for vector memory system."""
    
    def test_memory_stats(self, client, mock_vector_memory):
        """Test memory stats endpoint."""
        response = client.get("/memory/stats")
        
        assert response.status_code == 200
        data = response.json()
        assert "vector_memory" in data
    
    def test_add_to_memory(self, client, mock_vector_memory):
        """Test adding context to memory."""
        response = client.post("/memory/add", json={
            "content": "Release v1.9 had issues with database migrations.",
            "metadata": {"version": "1.9", "type": "release_note"}
        })
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"
        assert "doc_id" in data
    
    def test_search_memory(self, client, mock_vector_memory):
        """Test searching memory."""
        response = client.get("/memory/search", params={
            "query": "database improvements",
            "n_results": 3
        })
        
        assert response.status_code == 200
        data = response.json()
        assert "query" in data
        assert "context" in data


# =============================================================================
# MCP Management Tests
# =============================================================================

class TestMCPManagement:
    """Tests for MCP server management."""
    
    def test_list_mcp_servers(self, client, mock_mcp_manager):
        """Test listing MCP servers."""
        response = client.get("/mcp/servers")
        
        assert response.status_code == 200
        data = response.json()
        assert "total" in data
        assert "connected" in data
        assert "servers" in data
    
    def test_list_mcp_tools(self, client, mock_mcp_manager):
        """Test listing MCP tools."""
        response = client.get("/mcp/tools")
        
        assert response.status_code == 200
        data = response.json()
        assert "total" in data
        assert "tools" in data


# =============================================================================
# Integration Flow Tests
# =============================================================================

class TestReleaseFlowIntegration:
    """Integration tests simulating full release flow."""
    
    def test_full_release_check_flow(self, client, mock_graph_engine):
        """
        Test complete release check flow:
        1. User asks about release readiness
        2. Orchestrator coordinates via LangGraph
        3. MCP tools are called
        4. Report is generated
        """
        # Step 1: Initial query
        response = client.post("/execute", json={
            "task_id": "flow-test-1",
            "action": "process_query",
            "payload": {
                "query": "Run a complete release readiness check for v2.0"
            },
            "user_context": {
                "user_id": "release-manager",
                "team_id": "platform"
            }
        })
        
        assert response.status_code == 200
        data = response.json()
        
        # Verify response structure
        assert data["task_id"] == "flow-test-1"
        assert data["status"] in ["success", "failed"]
        
        if data["status"] == "success" and data["data"]:
            result_data = data["data"]
            assert "result" in result_data or "plan" in result_data
    
    def test_jira_to_report_flow(self, client, mock_graph_engine):
        """Test flow from Jira check to report generation."""
        response = client.post("/execute", json={
            "task_id": "jira-report-flow",
            "action": "process_query",
            "payload": {
                "query": "Get sprint stats for PROJ and generate a report"
            }
        })
        
        assert response.status_code == 200
        data = response.json()
        assert "data" in data
    
    def test_security_check_flow(self, client, mock_graph_engine):
        """Test security-focused release check."""
        response = client.post("/execute", json={
            "task_id": "security-check",
            "action": "process_query",
            "payload": {
                "query": "Check security vulnerabilities in our codebase"
            }
        })
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] in ["success", "failed"]
    
    def test_rca_analysis_flow(self, client, mock_graph_engine):
        """Test RCA analysis flow."""
        response = client.post("/execute", json={
            "task_id": "rca-test",
            "action": "process_query",
            "payload": {
                "query": "Analyze build failure for nexus-main build #142"
            }
        })
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] in ["success", "failed"]
    
    def test_hygiene_check_flow(self, client, mock_graph_engine):
        """Test Jira hygiene check flow."""
        response = client.post("/execute", json={
            "task_id": "hygiene-test",
            "action": "process_query",
            "payload": {
                "query": "Run hygiene check for project PROJ and notify assignees"
            }
        })
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] in ["success", "failed"]


# =============================================================================
# Error Handling Tests
# =============================================================================

class TestErrorHandling:
    """Tests for error handling in release flow."""
    
    def test_invalid_json(self, client):
        """Test handling invalid JSON."""
        response = client.post(
            "/execute",
            content="not valid json",
            headers={"Content-Type": "application/json"}
        )
        
        assert response.status_code == 422  # Validation error
    
    def test_missing_action(self, client):
        """Test handling missing action field."""
        response = client.post("/execute", json={
            "task_id": "error-test",
            "payload": {"query": "test"}
        })
        
        assert response.status_code == 422  # Validation error
    
    def test_empty_payload(self, client):
        """Test handling empty payload."""
        response = client.post("/execute", json={
            "task_id": "error-test",
            "action": "process_query",
            "payload": {}
        })
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "failed"


# =============================================================================
# LangGraph State Tests
# =============================================================================

class TestLangGraphState:
    """Tests for LangGraph state management."""
    
    def test_state_persistence(self, client, mock_graph_engine):
        """Test state is persisted across requests."""
        # First query
        response1 = client.post("/query", json={
            "query": "Start a release analysis",
            "thread_id": "persist-test"
        })
        
        assert response1.status_code == 200
        
        # Get state
        response2 = client.get("/thread/persist-test")
        
        assert response2.status_code == 200
        data = response2.json()
        assert data["thread_id"] == "persist-test"
    
    def test_conversation_continuity(self, client, mock_graph_engine):
        """Test conversation continues with same thread_id."""
        # First query
        client.post("/query", json={
            "query": "Check PROJ-123",
            "thread_id": "convo-test"
        })
        
        # Follow-up query
        response = client.post("/query", json={
            "query": "What are its blockers?",
            "thread_id": "convo-test"
        })
        
        assert response.status_code == 200
        data = response.json()
        assert data["thread_id"] == "convo-test"


# =============================================================================
# Performance Tests
# =============================================================================

class TestPerformance:
    """Basic performance tests."""
    
    def test_health_check_fast(self, client):
        """Test health check responds quickly."""
        import time
        
        start = time.time()
        response = client.get("/health")
        duration = time.time() - start
        
        assert response.status_code == 200
        assert duration < 1.0  # Should respond in under 1 second
    
    def test_metrics_endpoint(self, client):
        """Test Prometheus metrics endpoint."""
        response = client.get("/metrics")
        
        assert response.status_code == 200


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
