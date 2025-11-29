import pytest
from unittest.mock import AsyncMock, patch
import sys
import os
sys.path.append(os.path.abspath("services/orchestrator"))
sys.path.append(os.path.abspath("shared"))
from app.core.react_engine import ReActEngine

@pytest.mark.asyncio
async def test_react_plan():
    engine = ReActEngine(memory_client=AsyncMock())
    result = await engine.run("Check jira", {})
    assert "plan" in result
