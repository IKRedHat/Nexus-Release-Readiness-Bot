"""
Pytest Configuration and Fixtures

Provides shared fixtures for testing the Admin Dashboard backend.
"""

import os
import pytest
from typing import Generator, AsyncGenerator
from fastapi.testclient import TestClient
from httpx import AsyncClient
import asyncio

# Set test environment
os.environ["USE_SQLITE"] = "true"
os.environ["SQLITE_URL"] = "sqlite:///./test_nexus.db"
os.environ["NEXUS_JWT_SECRET"] = "test-secret-key-for-testing"
os.environ["NEXUS_ADMIN_EMAIL"] = "admin@test.nexus.dev"

# Import after setting environment
from main import app
from db.session import engine, SessionLocal, init_db, Base


@pytest.fixture(scope="session")
def event_loop():
    """Create event loop for async tests."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="session", autouse=True)
def setup_database():
    """Set up test database once for all tests."""
    # Create all tables
    Base.metadata.create_all(bind=engine)
    yield
    # Clean up after all tests
    Base.metadata.drop_all(bind=engine)
    # Remove test database file
    if os.path.exists("./test_nexus.db"):
        os.remove("./test_nexus.db")


@pytest.fixture
def db_session() -> Generator:
    """Create a new database session for a test."""
    session = SessionLocal()
    try:
        yield session
    finally:
        session.rollback()
        session.close()


@pytest.fixture
def client() -> Generator:
    """Create a test client for the FastAPI app."""
    with TestClient(app) as test_client:
        yield test_client


@pytest.fixture
async def async_client() -> AsyncGenerator:
    """Create an async test client."""
    async with AsyncClient(app=app, base_url="http://test") as ac:
        yield ac


@pytest.fixture
def auth_headers(client: TestClient) -> dict:
    """
    Get authentication headers for a logged-in admin user.
    
    Performs login and returns headers with JWT token.
    """
    # Login as admin
    response = client.post(
        "/auth/login",
        json={
            "email": "admin@nexus.dev",
            "password": "admin123"  # Default admin password
        }
    )
    
    if response.status_code != 200:
        # Create admin user if doesn't exist
        response = client.post(
            "/auth/login",
            json={
                "email": "admin@nexus.dev",
                "password": ""  # Empty password for local dev
            }
        )
    
    if response.status_code == 200:
        token = response.json().get("access_token")
        return {"Authorization": f"Bearer {token}"}
    
    # Fallback - no auth required in test mode
    return {}


@pytest.fixture
def sample_release() -> dict:
    """Sample release data for testing."""
    return {
        "version": "v1.0.0-test",
        "name": "Test Release",
        "target_date": "2024-12-31T10:00:00Z",
        "status": "planning",
        "description": "Test release for integration testing",
    }


@pytest.fixture
def sample_user() -> dict:
    """Sample user data for testing."""
    return {
        "email": "test.user@nexus.dev",
        "name": "Test User",
        "roles": ["developer"],
        "status": "active",
    }


@pytest.fixture
def sample_role() -> dict:
    """Sample role data for testing."""
    return {
        "name": "Test Role",
        "description": "A test role for integration testing",
        "permissions": ["releases:read", "releases:create"],
    }


@pytest.fixture
def sample_feature_request() -> dict:
    """Sample feature request data for testing."""
    return {
        "title": "Test Feature Request",
        "description": "A test feature request for integration testing",
        "priority": "medium",
        "type": "feature",
    }


# =============================================================================
# Utility Functions
# =============================================================================

def create_test_user(client: TestClient, user_data: dict) -> dict:
    """Helper to create a test user."""
    response = client.post("/users", json=user_data)
    return response.json()


def create_test_release(client: TestClient, release_data: dict, headers: dict = None) -> dict:
    """Helper to create a test release."""
    response = client.post("/releases", json=release_data, headers=headers or {})
    return response.json()

