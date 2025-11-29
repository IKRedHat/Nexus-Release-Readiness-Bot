import pytest
from fastapi.testclient import TestClient
import sys
import os
sys.path.append(os.path.abspath("services/orchestrator"))
sys.path.append(os.path.abspath("shared"))
from main import app

client = TestClient(app)

def test_health_check():
    response = client.get("/health")
    assert response.status_code == 200
