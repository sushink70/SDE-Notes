import pytest
from unittest.mock import Mock, patch
from models import User, APIClient

@pytest.fixture
def sample_user():
    """Create a sample user for testing"""
    return User(user_id=1, username="testuser", email="test@example.com")

@pytest.fixture
def users_list():
    """Create a list of users for bulk testing"""
    users = []
    for i in range(1, 4):
        user = User(
            user_id=i,
            username=f"user{i}",
            email=f"user{i}@example.com"
        )
        users.append(user)
    return users

@pytest.fixture
def api_client():
    """Create an API client for testing"""
    return APIClient("https://api.example.com")

@pytest.fixture
def mock_requests():
    """Mock requests module"""
    with patch('models.requests') as mock:
        yield mock