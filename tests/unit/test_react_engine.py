"""
Unit Tests for ReAct Engine
Tests the orchestrator's reasoning and action execution
"""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
import sys
import os

sys.path.insert(0, os.path.abspath("services/orchestrator"))
sys.path.insert(0, os.path.abspath("shared"))

from app.core.react_engine import ReActEngine, AVAILABLE_TOOLS, get_tools_description
from app.core.memory import VectorMemory


class TestReActEngine:
    """Tests for the ReAct Engine"""
    
    @pytest.fixture
    def react_engine(self, mock_vector_memory):
        """Create ReAct engine instance"""
        engine = ReActEngine(memory_client=mock_vector_memory, max_iterations=5)
        return engine
    
    def test_tools_registered(self):
        """Test that all expected tools are registered"""
        expected_tools = [
            "get_jira_ticket",
            "get_ticket_hierarchy",
            "search_jira",
            "update_jira_ticket",
            "get_sprint_stats",
            "get_repo_health",
            "get_pr_status",
            "get_build_status",
            "trigger_build",
            "get_security_scan",
            "generate_report",
            "publish_report",
            "analyze_readiness",
            "send_slack_notification"
        ]
        
        for tool in expected_tools:
            assert tool in AVAILABLE_TOOLS, f"Tool {tool} not registered"
    
    def test_tools_have_descriptions(self):
        """Test all tools have descriptions"""
        for name, tool in AVAILABLE_TOOLS.items():
            assert tool.description, f"Tool {name} missing description"
            assert len(tool.description) > 10, f"Tool {name} description too short"
    
    def test_get_tools_description(self):
        """Test tools description generation"""
        description = get_tools_description()
        
        assert "Available tools:" in description
        assert "get_jira_ticket" in description
        assert "get_security_scan" in description
    
    @pytest.mark.asyncio
    async def test_react_run_simple_query(self, react_engine, mock_final_answer_response):
        """Test running a simple query that gets immediate answer"""
        with patch.object(react_engine.llm, 'generate', new_callable=AsyncMock) as mock_llm:
            mock_llm.return_value = mock_final_answer_response
            
            result = await react_engine.run(
                "What is 2+2?",
                {"user_id": "test"}
            )
            
            assert "result" in result
            assert "steps" in result
            assert result["steps"] >= 1
    
    @pytest.mark.asyncio
    async def test_react_run_with_tool_call(self, react_engine, mock_llm_response, mock_final_answer_response):
        """Test running a query that requires tool calls"""
        with patch.object(react_engine.llm, 'generate', new_callable=AsyncMock) as mock_llm:
            # First call returns action, second returns final answer
            mock_llm.side_effect = [mock_llm_response, mock_final_answer_response]
            
            with patch.object(react_engine, '_execute_tool', new_callable=AsyncMock) as mock_tool:
                mock_tool.return_value = {"status": "success", "data": {"key": "PROJ-123"}}
                
                result = await react_engine.run(
                    "Check ticket PROJ-123",
                    {"user_id": "test"}
                )
                
                assert "result" in result
                assert result["steps"] >= 1
    
    @pytest.mark.asyncio
    async def test_max_iterations_limit(self, react_engine, mock_llm_response):
        """Test that max iterations prevents infinite loops"""
        react_engine.max_iterations = 3
        
        with patch.object(react_engine.llm, 'generate', new_callable=AsyncMock) as mock_llm:
            # Always return action (never final answer) to test iteration limit
            mock_llm.return_value = mock_llm_response
            
            with patch.object(react_engine, '_execute_tool', new_callable=AsyncMock) as mock_tool:
                mock_tool.return_value = {"status": "success"}
                
                result = await react_engine.run(
                    "Loop forever",
                    {"user_id": "test"}
                )
                
                assert result["steps"] == 3
                assert "max_iterations" in str(result.get("error", ""))
    
    def test_parse_llm_response_action(self, react_engine):
        """Test parsing LLM response with action"""
        response = """Thought: I need to check the ticket.
Action: get_jira_ticket
Action Input: {"ticket_key": "PROJ-123"}"""
        
        parsed = react_engine._parse_llm_response(response)
        
        assert parsed["thought"] == "I need to check the ticket."
        assert parsed["action"] == "get_jira_ticket"
        assert parsed["action_input"] == {"ticket_key": "PROJ-123"}
        assert parsed["final_answer"] is None
    
    def test_parse_llm_response_final_answer(self, react_engine):
        """Test parsing LLM response with final answer"""
        response = """Thought: I have all the information.
Final Answer: The release is ready to go."""
        
        parsed = react_engine._parse_llm_response(response)
        
        assert parsed["thought"] == "I have all the information."
        assert parsed["final_answer"] == "The release is ready to go."
        assert parsed["action"] is None
    
    def test_classify_query(self, react_engine):
        """Test query classification for metrics"""
        assert react_engine._classify_query("Is the release ready?") == "release_check"
        assert react_engine._classify_query("Check ticket PROJ-123") == "jira_query"
        assert react_engine._classify_query("Build status?") == "ci_query"
        assert react_engine._classify_query("Security scan results") == "security_query"
        assert react_engine._classify_query("Generate a report") == "report"
        assert react_engine._classify_query("Hello world") == "general"
    
    @pytest.mark.asyncio
    async def test_execute_tool_unknown(self, react_engine):
        """Test executing unknown tool returns error"""
        result = await react_engine._execute_tool("unknown_tool", {})
        
        assert "error" in result
        assert "Unknown tool" in result["error"]


class TestVectorMemory:
    """Tests for Vector Memory"""
    
    @pytest.fixture
    def memory(self):
        """Create memory instance"""
        return VectorMemory()
    
    @pytest.mark.asyncio
    async def test_add_and_retrieve(self, memory):
        """Test adding and retrieving context"""
        await memory.add_context(
            doc_id="test-doc-1",
            text="Release v1.0 had database issues",
            metadata={"version": "1.0"}
        )
        
        result = await memory.retrieve("database problems")
        
        assert result  # Should return some context
    
    @pytest.mark.asyncio
    async def test_mock_context(self, memory):
        """Test mock context generation"""
        result = await memory.retrieve("release history")
        
        assert "RELEVANT HISTORICAL CONTEXT" in result or result == ""
    
    @pytest.mark.asyncio
    async def test_get_stats(self, memory):
        """Test memory stats"""
        stats = await memory.get_stats()
        
        assert "backend" in stats
        assert "count" in stats


class TestLLMClient:
    """Tests for LLM Client"""
    
    def test_mock_mode_default(self):
        """Test LLM client defaults to mock mode"""
        from app.core.react_engine import LLMClient
        
        client = LLMClient()
        assert client.provider == "mock"
    
    @pytest.mark.asyncio
    async def test_mock_generate(self):
        """Test mock LLM generation"""
        from app.core.react_engine import LLMClient
        
        client = LLMClient()
        result = await client.generate("Check jira ticket PROJ-123")
        
        assert "content" in result
        assert "input_tokens" in result
        assert "output_tokens" in result
    
    @pytest.mark.asyncio
    async def test_mock_generate_jira_query(self):
        """Test mock generates Jira-related response"""
        from app.core.react_engine import LLMClient
        
        client = LLMClient()
        result = await client.generate("What is the status of PROJ-123?")
        
        assert "Thought:" in result["content"]
        assert "Action" in result["content"] or "Final Answer" in result["content"]
