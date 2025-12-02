"""
Tests for the users module.
"""
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_get_users():
    """Test getting all users."""
    response = client.get("/users/")
    assert response.status_code == 200
    # TODO: Add more specific assertions based on your implementation


def test_get_user():
    """Test getting a specific user."""
    user_id = 1
    response = client.get(f"/users/{user_id}")
    assert response.status_code == 200
    # TODO: Add more specific assertions based on your implementation



