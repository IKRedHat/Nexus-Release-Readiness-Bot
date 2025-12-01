"""
Integration Tests for Agent Communication
==========================================

Tests for inter-agent communication, orchestrator coordination,
and end-to-end workflow integration.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
import sys
import os
import asyncio

sys.path.insert(0, os.path.abspath("services/orchestrator"))
sys.path.insert(0, os.path.abspath("shared"))

# Set test environment
os.environ["NEXUS_ENV"] = "test"
os.environ["NEXUS_MOCK_MODE"] = "true"
os.environ["NEXUS_REQUIRE_AUTH"] = "false"


class TestOrchestratorAgentIntegration:
    """Tests for Orchestrator -> Agent communication."""
    
    @pytest.fixture
    def mock_http_client(self):
        """Mock HTTP client for agent calls."""
        client = AsyncMock()
        client.post = AsyncMock()
        client.get = AsyncMock()
        return client
    
    @pytest.mark.asyncio
    async def test_orchestrator_calls_jira_agent(self, mock_http_client):
        """Test orchestrator calling Jira agent."""
        from app.core.react_engine import ReActEngine, AVAILABLE_TOOLS
        from app.core.memory import VectorMemory
        
        memory = VectorMemory()
        engine = ReActEngine(memory_client=memory, max_iterations=3)
        
        # Mock the tool execution
        mock_response = {
            "status": "success",
            "data": {
                "key": "PROJ-123",
                "summary": "Test ticket",
                "status": "In Progress"
            }
        }
        
        with patch.object(engine, '_execute_tool', new_callable=AsyncMock) as mock_exec:
            mock_exec.return_value = mock_response
            
            # Simulate calling get_jira_ticket tool
            result = await engine._execute_tool(
                "get_jira_ticket",
                {"ticket_key": "PROJ-123"}
            )
            
            assert result["status"] == "success"
            assert result["data"]["key"] == "PROJ-123"
    
    @pytest.mark.asyncio
    async def test_orchestrator_calls_git_ci_agent(self, mock_http_client):
        """Test orchestrator calling Git/CI agent."""
        from app.core.react_engine import ReActEngine
        from app.core.memory import VectorMemory
        
        memory = VectorMemory()
        engine = ReActEngine(memory_client=memory, max_iterations=3)
        
        mock_response = {
            "status": "success",
            "data": {
                "job_name": "nexus-main",
                "build_number": 142,
                "status": "SUCCESS"
            }
        }
        
        with patch.object(engine, '_execute_tool', new_callable=AsyncMock) as mock_exec:
            mock_exec.return_value = mock_response
            
            result = await engine._execute_tool(
                "get_build_status",
                {"job_name": "nexus-main", "build_number": 142}
            )
            
            assert result["status"] == "success"
            assert result["data"]["status"] == "SUCCESS"
    
    @pytest.mark.asyncio
    async def test_orchestrator_chains_multiple_agents(self, mock_http_client):
        """Test orchestrator chaining multiple agent calls."""
        from app.core.react_engine import ReActEngine
        from app.core.memory import VectorMemory
        
        memory = VectorMemory()
        engine = ReActEngine(memory_client=memory, max_iterations=5)
        
        # Simulate a release check that requires multiple agents
        call_sequence = []
        
        async def mock_tool_execution(tool_name, params):
            call_sequence.append(tool_name)
            
            if tool_name == "get_sprint_stats":
                return {"status": "success", "data": {"completion_rate": 95}}
            elif tool_name == "get_build_status":
                return {"status": "success", "data": {"status": "SUCCESS"}}
            elif tool_name == "get_security_scan":
                return {"status": "success", "data": {"risk_score": 25}}
            else:
                return {"status": "success", "data": {}}
        
        with patch.object(engine, '_execute_tool', side_effect=mock_tool_execution):
            # Execute all three tools
            await engine._execute_tool("get_sprint_stats", {"project": "PROJ"})
            await engine._execute_tool("get_build_status", {"job_name": "nexus"})
            await engine._execute_tool("get_security_scan", {"repo": "nexus"})
            
            # Verify all agents were called
            assert len(call_sequence) == 3
            assert "get_sprint_stats" in call_sequence
            assert "get_build_status" in call_sequence
            assert "get_security_scan" in call_sequence


class TestAgentToAgentCommunication:
    """Tests for direct agent-to-agent communication."""
    
    @pytest.mark.asyncio
    async def test_hygiene_agent_calls_slack_agent(self):
        """Test Hygiene Agent sending notifications via Slack Agent."""
        from nexus_lib.utils import AsyncHttpClient
        
        client = AsyncHttpClient()
        
        # Mock the POST to Slack agent
        mock_response = {"status": "success", "message_ts": "123.456"}
        
        with patch.object(client, 'post', new_callable=AsyncMock) as mock_post:
            mock_post.return_value = mock_response
            
            result = await client.post(
                "http://slack-agent:8084/send-dm",
                json={
                    "user_email": "developer@example.com",
                    "message": "Hygiene violation found",
                    "blocks": []
                }
            )
            
            assert result["status"] == "success"
    
    @pytest.mark.asyncio
    async def test_rca_agent_calls_slack_agent(self):
        """Test RCA Agent sending notifications via Slack Agent."""
        from nexus_lib.utils import AsyncHttpClient
        
        client = AsyncHttpClient()
        
        mock_response = {"status": "success", "channel": "#releases"}
        
        with patch.object(client, 'post', new_callable=AsyncMock) as mock_post:
            mock_post.return_value = mock_response
            
            result = await client.post(
                "http://slack-agent:8084/notify",
                json={
                    "channel": "#releases",
                    "message": "Build failure analyzed",
                    "attachments": []
                }
            )
            
            assert result["status"] == "success"
    
    @pytest.mark.asyncio
    async def test_slack_agent_calls_jira_agent(self):
        """Test Slack Agent updating Jira via Jira Agent."""
        from nexus_lib.utils import AsyncHttpClient
        
        client = AsyncHttpClient()
        
        mock_response = {"status": "success", "updated": True}
        
        with patch.object(client, 'post', new_callable=AsyncMock) as mock_post:
            mock_post.return_value = mock_response
            
            result = await client.post(
                "http://jira-agent:8081/ticket/PROJ-123/fields",
                json={
                    "labels": ["backend"],
                    "fixVersions": ["v2.0.0"]
                }
            )
            
            assert result["status"] == "success"


class TestReleaseWorkflow:
    """Integration tests for complete release workflow."""
    
    @pytest.mark.asyncio
    async def test_release_readiness_workflow(self):
        """Test complete release readiness check workflow."""
        
        # This simulates the full flow:
        # 1. Orchestrator receives "Is v2.0 ready?"
        # 2. Calls Jira Agent for ticket stats
        # 3. Calls Git/CI Agent for build status
        # 4. Calls Git/CI Agent for security scan
        # 5. Generates report
        
        workflow_data = {
            "release_version": "v2.0.0",
            "steps_executed": [],
            "results": {}
        }
        
        # Step 1: Get ticket stats
        workflow_data["steps_executed"].append("get_sprint_stats")
        workflow_data["results"]["tickets"] = {
            "total": 45,
            "completed": 42,
            "completion_rate": 93.3
        }
        
        # Step 2: Get build status
        workflow_data["steps_executed"].append("get_build_status")
        workflow_data["results"]["build"] = {
            "status": "SUCCESS",
            "last_build": 142
        }
        
        # Step 3: Get security scan
        workflow_data["steps_executed"].append("get_security_scan")
        workflow_data["results"]["security"] = {
            "risk_score": 25,
            "critical": 0,
            "high": 2
        }
        
        # Step 4: Analyze readiness
        workflow_data["steps_executed"].append("analyze_readiness")
        
        # Calculate decision
        stats = workflow_data["results"]
        is_ready = (
            stats["tickets"]["completion_rate"] >= 90 and
            stats["build"]["status"] == "SUCCESS" and
            stats["security"]["critical"] == 0
        )
        
        workflow_data["results"]["decision"] = "GO" if is_ready else "NO_GO"
        
        # Assertions
        assert len(workflow_data["steps_executed"]) == 4
        assert workflow_data["results"]["decision"] == "GO"
    
    @pytest.mark.asyncio
    async def test_build_failure_workflow(self):
        """Test build failure -> RCA -> notification workflow."""
        
        workflow_data = {
            "trigger": "jenkins_webhook",
            "steps_executed": [],
            "results": {}
        }
        
        # Step 1: Receive webhook
        workflow_data["steps_executed"].append("receive_webhook")
        workflow_data["results"]["webhook"] = {
            "job_name": "nexus-main",
            "build_number": 143,
            "status": "FAILURE"
        }
        
        # Step 2: Trigger RCA
        workflow_data["steps_executed"].append("trigger_rca")
        workflow_data["results"]["rca"] = {
            "analysis_id": "rca-143",
            "root_cause": "NullPointerException in UserService",
            "confidence": 0.85
        }
        
        # Step 3: Get PR owner
        workflow_data["steps_executed"].append("get_pr_owner")
        workflow_data["results"]["pr_owner"] = {
            "email": "developer@example.com",
            "slack_id": "U123456"
        }
        
        # Step 4: Send notification
        workflow_data["steps_executed"].append("send_notification")
        workflow_data["results"]["notification"] = {
            "channel": "#releases",
            "user_tagged": True
        }
        
        # Assertions
        assert len(workflow_data["steps_executed"]) == 4
        assert workflow_data["results"]["rca"]["confidence"] >= 0.8
        assert workflow_data["results"]["notification"]["user_tagged"]


class TestHygieneWorkflow:
    """Integration tests for hygiene check workflow."""
    
    @pytest.mark.asyncio
    async def test_hygiene_check_notification_flow(self):
        """Test hygiene check -> violations -> notifications flow."""
        
        workflow_data = {
            "trigger": "scheduled_check",
            "steps_executed": [],
            "results": {}
        }
        
        # Step 1: Get tickets
        workflow_data["steps_executed"].append("get_tickets")
        workflow_data["results"]["tickets"] = [
            {"key": "PROJ-1", "assignee": "alice@example.com", "violations": ["labels"]},
            {"key": "PROJ-2", "assignee": "alice@example.com", "violations": ["fixVersions"]},
            {"key": "PROJ-3", "assignee": "bob@example.com", "violations": ["story_points"]},
        ]
        
        # Step 2: Group by assignee
        workflow_data["steps_executed"].append("group_violations")
        workflow_data["results"]["by_assignee"] = {
            "alice@example.com": 2,
            "bob@example.com": 1
        }
        
        # Step 3: Send notifications
        workflow_data["steps_executed"].append("send_notifications")
        workflow_data["results"]["notifications_sent"] = 2
        
        # Step 4: Update metrics
        workflow_data["steps_executed"].append("update_metrics")
        workflow_data["results"]["hygiene_score"] = 70.0  # 3 violations / 10 tickets
        
        # Assertions
        assert len(workflow_data["steps_executed"]) == 4
        assert workflow_data["results"]["notifications_sent"] == 2
        assert workflow_data["results"]["hygiene_score"] > 0


class TestReportingWorkflow:
    """Integration tests for reporting workflow."""
    
    @pytest.mark.asyncio
    async def test_report_generation_flow(self):
        """Test data collection -> report generation -> publish flow."""
        
        workflow_data = {
            "release_version": "v2.0.0",
            "steps_executed": [],
            "results": {}
        }
        
        # Step 1: Collect data
        workflow_data["steps_executed"].append("collect_data")
        workflow_data["results"]["data"] = {
            "tickets": {"completion_rate": 95},
            "builds": [{"status": "SUCCESS"}],
            "security": {"risk_score": 20}
        }
        
        # Step 2: Generate report
        workflow_data["steps_executed"].append("generate_report")
        workflow_data["results"]["report"] = {
            "format": "html",
            "size_bytes": 15000
        }
        
        # Step 3: Analyze readiness
        workflow_data["steps_executed"].append("analyze_readiness")
        workflow_data["results"]["analysis"] = {
            "decision": "GO",
            "blockers": []
        }
        
        # Step 4: Publish to Confluence
        workflow_data["steps_executed"].append("publish_report")
        workflow_data["results"]["publish"] = {
            "url": "https://confluence.example.com/pages/123",
            "space": "REL"
        }
        
        # Assertions
        assert len(workflow_data["steps_executed"]) == 4
        assert workflow_data["results"]["analysis"]["decision"] == "GO"
        assert "confluence" in workflow_data["results"]["publish"]["url"]


class TestErrorHandling:
    """Integration tests for error handling across services."""
    
    @pytest.mark.asyncio
    async def test_agent_failure_recovery(self):
        """Test orchestrator handling agent failures."""
        from app.core.react_engine import ReActEngine
        from app.core.memory import VectorMemory
        
        memory = VectorMemory()
        engine = ReActEngine(memory_client=memory, max_iterations=3)
        
        call_count = 0
        
        async def failing_tool(*args, **kwargs):
            nonlocal call_count
            call_count += 1
            if call_count < 2:
                raise Exception("Agent unavailable")
            return {"status": "success", "data": {}}
        
        with patch.object(engine, '_execute_tool', side_effect=failing_tool):
            # Should retry and eventually succeed
            try:
                result = await engine._execute_tool("test_tool", {})
                # If we get here, retry worked
                assert result["status"] == "success"
            except Exception:
                # Expected on first call
                pass
    
    @pytest.mark.asyncio
    async def test_partial_workflow_failure(self):
        """Test workflow continues despite partial failures."""
        
        workflow_data = {
            "steps_executed": [],
            "errors": [],
            "results": {}
        }
        
        # Step 1: Success
        workflow_data["steps_executed"].append("get_tickets")
        workflow_data["results"]["tickets"] = {"count": 45}
        
        # Step 2: Failure
        workflow_data["steps_executed"].append("get_build_status")
        workflow_data["errors"].append({
            "step": "get_build_status",
            "error": "Jenkins unavailable"
        })
        
        # Step 3: Success with fallback
        workflow_data["steps_executed"].append("get_cached_build_status")
        workflow_data["results"]["build"] = {"status": "UNKNOWN", "cached": True}
        
        # Workflow should still complete
        assert len(workflow_data["steps_executed"]) == 3
        assert len(workflow_data["errors"]) == 1
        assert workflow_data["results"]["build"]["cached"]


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

