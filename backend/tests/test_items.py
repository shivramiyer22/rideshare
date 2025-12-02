"""
Tests for the items module.
"""
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_get_items():
    """Test getting all items."""
    response = client.get("/items/")
    assert response.status_code == 200
    # TODO: Add more specific assertions based on your implementation


def test_get_item():
    """Test getting a specific item."""
    item_id = 1
    response = client.get(f"/items/{item_id}")
    assert response.status_code == 200
    # TODO: Add more specific assertions based on your implementation



