import pytest
from datetime import datetime
import requests  # Import requests for real HTTPError
from models import User, APIClient
from unittest.mock import Mock

# --- Tests for User class ---

def test_user_initialization(sample_user):
    """Test that a User object is initialized correctly."""
    assert sample_user.user_id == 1
    assert sample_user.username == "testuser"
    assert sample_user.email == "test@example.com"
    assert isinstance(sample_user.created_at, datetime)
    assert sample_user.posts == []

def test_add_post(sample_user):
    """Test adding a post to a user."""
    post = sample_user.add_post(title="Test Post", content="This is a test post")
    
    assert len(sample_user.posts) == 1
    assert post["id"] == 1
    assert post["title"] == "Test Post"
    assert post["content"] == "This is a test post"
    assert post["author"] == sample_user.username
    assert isinstance(post["created_at"], datetime)

def test_get_posts(sample_user):
    """Test retrieving posts and verify it returns a copy."""
    sample_user.add_post(title="Post 1", content="Content 1")
    sample_user.add_post(title="Post 2", content="Content 2")
    
    posts = sample_user.get_posts()
    assert len(posts) == 2
    assert posts[0]["title"] == "Post 1"
    assert posts[1]["title"] == "Post 2"
    
    # Verify that get_posts returns a copy, not the original list
    posts.append({"id": 3, "title": "Fake Post", "content": "Fake", "author": "testuser", "created_at": datetime.now()})
    assert len(sample_user.posts) == 2  # Original list should be unchanged

def test_users_list(users_list):
    """Test the users_list fixture for correct initialization."""
    assert len(users_list) == 3
    assert users_list[0].username == "user1"
    assert users_list[1].email == "user2@example.com"
    assert users_list[2].user_id == 3

# --- Tests for APIClient class ---

def test_get_user_data(api_client, mock_requests):
    """Test getting user data from the API."""
    # Mock the GET response
    mock_response = Mock()
    mock_response.json.return_value = {
        "user_id": 1,
        "username": "testuser",
        "email": "test@example.com"
    }
    mock_response.raise_for_status.return_value = None
    mock_requests.get.return_value = mock_response

    # Call the method
    result = api_client.get_user_data(user_id=1)
    
    # Verify the request
    mock_requests.get.assert_called_once_with("https://api.example.com/users/1")
    assert result == {
        "user_id": 1,
        "username": "testuser",
        "email": "test@example.com"
    }

def test_get_user_data_error(api_client, mock_requests):
    """Test handling of HTTP errors in get_user_data."""
    # Mock an HTTP error
    mock_response = Mock()
    mock_response.raise_for_status.side_effect = requests.exceptions.HTTPError("404 Not Found")
    mock_requests.get.return_value = mock_response

    # Verify that the error is raised
    with pytest.raises(requests.exceptions.HTTPError):
        api_client.get_user_data(user_id=999)

def test_create_user(api_client, mock_requests):
    """Test creating a user via the API."""
    # Mock the POST response
    mock_response = Mock()
    mock_response.json.return_value = {
        "user_id": 2,
        "username": "newuser",
        "email": "newuser@example.com"
    }
    mock_response.raise_for_status.return_value = None
    mock_requests.post.return_value = mock_response

    # Input data
    user_data = {
        "username": "newuser",
        "email": "newuser@example.com"
    }

    # Call the method
    result = api_client.create_user(user_data=user_data)
    
    # Verify the request
    mock_requests.post.assert_called_once_with(
        "https://api.example.com/users",
        json=user_data
    )
    assert result == {
        "user_id": 2,
        "username": "newuser",
        "email": "newuser@example.com"
    }

def test_create_user_error(api_client, mock_requests):
    """Test handling of HTTP errors in create_user."""
    # Mock an HTTP error
    mock_response = Mock()
    mock_response.raise_for_status.side_effect = requests.exceptions.HTTPError("400 Bad Request")
    mock_requests.post.return_value = mock_response

    # Input data
    user_data = {
        "username": "invaliduser",
        "email": "invalid@example.com"
    }

    # Verify that the error is raised
    with pytest.raises(requests.exceptions.HTTPError):
        api_client.create_user(user_data=user_data)