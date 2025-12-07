"""
Comprehensive Endpoint Tests for Rideshare Backend API

Tests all implemented endpoints:
- Analytics: /dashboard, /metrics, /revenue
- Chatbot: /chat, /history
- Users: CRUD operations
- Orders: CRUD operations
- ML: /train, /forecast
- Upload: /historical-data, /competitor-data

Run with: pytest tests/test_all_endpoints.py -v
"""

import pytest
import httpx
import asyncio
from datetime import datetime
import uuid

# Base URL for the API
BASE_URL = "http://localhost:8000/api/v1"


# ============================================================================
# FIXTURES
# ============================================================================

@pytest.fixture
def client():
    """Create a sync HTTP client for testing."""
    return httpx.Client(base_url=BASE_URL, timeout=30.0)


@pytest.fixture
def async_client():
    """Create an async HTTP client for testing."""
    return httpx.AsyncClient(base_url=BASE_URL, timeout=30.0)


# ============================================================================
# ANALYTICS ENDPOINT TESTS
# ============================================================================

class TestAnalyticsEndpoints:
    """Test analytics endpoints."""
    
    def test_get_dashboard(self, client):
        """Test GET /analytics/dashboard returns dashboard data."""
        response = client.get("/analytics/dashboard")
        assert response.status_code == 200
        
        data = response.json()
        assert "kpis" in data
        assert "pricing_breakdown" in data
        assert "loyalty_distribution" in data
        assert "period" in data
        
        # Verify KPIs structure
        kpis = data["kpis"]
        assert "total_revenue" in kpis
        assert "total_rides" in kpis
        assert "avg_ride_cost" in kpis
    
    def test_get_dashboard_with_dates(self, client):
        """Test GET /analytics/dashboard with date parameters."""
        response = client.get(
            "/analytics/dashboard",
            params={
                "start_date": "2024-01-01T00:00:00",
                "end_date": "2024-12-31T23:59:59"
            }
        )
        assert response.status_code == 200
        data = response.json()
        assert "period" in data
    
    def test_get_metrics(self, client):
        """Test GET /analytics/metrics returns key metrics."""
        response = client.get("/analytics/metrics")
        assert response.status_code == 200
        
        data = response.json()
        assert "metrics" in data
        assert "last_updated" in data
        
        metrics = data["metrics"]
        assert "total_rides" in metrics
        assert "total_revenue" in metrics
        assert "pending_orders" in metrics
    
    def test_get_revenue(self, client):
        """Test GET /analytics/revenue returns revenue analytics."""
        response = client.get("/analytics/revenue")
        assert response.status_code == 200
        
        data = response.json()
        assert "total_revenue" in data
        assert "total_rides" in data
        assert "period" in data
    
    def test_get_revenue_with_period(self, client):
        """Test GET /analytics/revenue with different periods."""
        for period in ["7d", "30d", "60d", "90d"]:
            response = client.get("/analytics/revenue", params={"period": period})
            assert response.status_code == 200
            data = response.json()
            assert data["period"] == period


# ============================================================================
# USERS ENDPOINT TESTS
# ============================================================================

class TestUsersEndpoints:
    """Test users CRUD endpoints."""
    
    @pytest.fixture
    def unique_user_data(self):
        """Generate unique user data for each test."""
        unique_id = uuid.uuid4().hex[:8]
        return {
            "email": f"test_{unique_id}@example.com",
            "username": f"testuser_{unique_id}",
            "full_name": "Test User",
            "loyalty_tier": "Silver"
        }
    
    def test_create_user(self, client, unique_user_data):
        """Test POST /users/ creates a new user."""
        response = client.post("/users/", json=unique_user_data)
        assert response.status_code == 200
        
        data = response.json()
        assert data["email"] == unique_user_data["email"]
        assert data["username"] == unique_user_data["username"]
        assert data["loyalty_tier"] == unique_user_data["loyalty_tier"]
        assert "id" in data
        assert data["id"].startswith("USR-")
    
    def test_get_users_list(self, client):
        """Test GET /users/ returns list of users."""
        response = client.get("/users/")
        assert response.status_code == 200
        
        data = response.json()
        assert isinstance(data, list)
    
    def test_get_users_with_filter(self, client):
        """Test GET /users/ with loyalty tier filter."""
        response = client.get("/users/", params={"loyalty_tier": "Gold"})
        assert response.status_code == 200
        
        data = response.json()
        assert isinstance(data, list)
        # All returned users should be Gold tier (if any)
        for user in data:
            assert user["loyalty_tier"] == "Gold"
    
    def test_get_user_by_id(self, client, unique_user_data):
        """Test GET /users/{user_id} returns specific user."""
        # First create a user
        create_response = client.post("/users/", json=unique_user_data)
        assert create_response.status_code == 200
        user_id = create_response.json()["id"]
        
        # Then get the user
        response = client.get(f"/users/{user_id}")
        assert response.status_code == 200
        
        data = response.json()
        assert data["id"] == user_id
        assert data["email"] == unique_user_data["email"]
    
    def test_get_user_not_found(self, client):
        """Test GET /users/{user_id} returns 404 for non-existent user."""
        response = client.get("/users/USR-NONEXISTENT")
        assert response.status_code == 404
    
    def test_update_user(self, client, unique_user_data):
        """Test PUT /users/{user_id} updates user."""
        # First create a user
        create_response = client.post("/users/", json=unique_user_data)
        assert create_response.status_code == 200
        user_id = create_response.json()["id"]
        
        # Update the user
        update_data = {"full_name": "Updated Name", "loyalty_tier": "Gold"}
        response = client.put(f"/users/{user_id}", json=update_data)
        assert response.status_code == 200
        
        data = response.json()
        assert data["full_name"] == "Updated Name"
        assert data["loyalty_tier"] == "Gold"
    
    def test_delete_user(self, client, unique_user_data):
        """Test DELETE /users/{user_id} soft deletes user."""
        # First create a user
        create_response = client.post("/users/", json=unique_user_data)
        assert create_response.status_code == 200
        user_id = create_response.json()["id"]
        
        # Delete the user
        response = client.delete(f"/users/{user_id}")
        assert response.status_code == 200
        
        data = response.json()
        assert "deleted" in data["message"].lower()
    
    def test_create_duplicate_email(self, client, unique_user_data):
        """Test POST /users/ rejects duplicate email."""
        # Create first user
        client.post("/users/", json=unique_user_data)
        
        # Try to create second user with same email
        response = client.post("/users/", json=unique_user_data)
        assert response.status_code == 400
        assert "already exists" in response.json()["detail"].lower()


# ============================================================================
# ORDERS ENDPOINT TESTS
# ============================================================================

class TestOrdersEndpoints:
    """Test orders CRUD endpoints."""
    
    @pytest.fixture
    def order_data(self):
        """Sample order data for testing."""
        return {
            "user_id": "test_user_123",
            "pickup_location": {"address": "123 Main St, Phoenix, AZ"},
            "dropoff_location": {"address": "456 Oak Ave, Scottsdale, AZ"},
            "pricing_tier": "STANDARD",
            "priority": "P1"
        }
    
    def test_create_order(self, client, order_data):
        """Test POST /orders/ creates a new order."""
        response = client.post("/orders/", json=order_data)
        assert response.status_code == 200
        
        data = response.json()
        assert data["user_id"] == order_data["user_id"]
        assert data["pricing_tier"] == "STANDARD"
        assert data["status"] == "PENDING"
        assert "id" in data
        assert data["id"].startswith("ORD-")
    
    def test_create_order_contracted(self, client):
        """Test creating CONTRACTED order assigns P0 priority."""
        order_data = {
            "user_id": "test_user_456",
            "pickup_location": {"address": "Airport Terminal"},
            "dropoff_location": {"address": "Downtown Hotel"},
            "pricing_tier": "CONTRACTED",
            "priority": "P2"  # Should be overridden to P0
        }
        response = client.post("/orders/", json=order_data)
        assert response.status_code == 200
        
        data = response.json()
        assert data["pricing_tier"] == "CONTRACTED"
        assert data["priority"] == "P0"  # Auto-assigned for CONTRACTED
    
    def test_create_order_custom(self, client):
        """Test creating CUSTOM order assigns P2 priority."""
        order_data = {
            "user_id": "test_user_789",
            "pickup_location": {"address": "Custom Location A"},
            "dropoff_location": {"address": "Custom Location B"},
            "pricing_tier": "CUSTOM",
            "priority": "P1"  # Should be overridden to P2
        }
        response = client.post("/orders/", json=order_data)
        assert response.status_code == 200
        
        data = response.json()
        assert data["pricing_tier"] == "CUSTOM"
        assert data["priority"] == "P2"  # Auto-assigned for CUSTOM
    
    def test_get_orders_list(self, client):
        """Test GET /orders/ returns list of orders."""
        response = client.get("/orders/")
        assert response.status_code == 200
        
        data = response.json()
        assert isinstance(data, list)
    
    def test_get_order_by_id(self, client, order_data):
        """Test GET /orders/{order_id} returns specific order."""
        # First create an order
        create_response = client.post("/orders/", json=order_data)
        assert create_response.status_code == 200
        order_id = create_response.json()["id"]
        
        # Then get the order
        response = client.get(f"/orders/{order_id}")
        assert response.status_code == 200
        
        data = response.json()
        assert data["id"] == order_id
    
    def test_get_order_not_found(self, client):
        """Test GET /orders/{order_id} returns 404 for non-existent order."""
        response = client.get("/orders/ORD-NONEXISTENT")
        assert response.status_code == 404
    
    def test_get_priority_queue(self, client):
        """Test GET /orders/queue/priority returns queue status."""
        response = client.get("/orders/queue/priority")
        assert response.status_code == 200
        
        data = response.json()
        assert "P0" in data
        assert "P1" in data
        assert "P2" in data
        assert "status" in data


# ============================================================================
# CHATBOT ENDPOINT TESTS
# ============================================================================

class TestChatbotEndpoints:
    """Test chatbot endpoints."""
    
    def test_chat_endpoint(self, client):
        """Test POST /chatbot/chat sends and receives message."""
        message_data = {
            "message": "Hello, what can you help me with?",
            "context": {"user_id": "test_user"}
        }
        response = client.post("/chatbot/chat", json=message_data)
        
        # Should return 200 or 503 if OPENAI_API_KEY not configured
        assert response.status_code in [200, 503]
        
        if response.status_code == 200:
            data = response.json()
            assert "response" in data
            assert "context" in data
            assert "thread_id" in data["context"]
    
    def test_chat_with_thread_id(self, client):
        """Test POST /chatbot/chat maintains conversation with thread_id."""
        thread_id = f"test_thread_{uuid.uuid4().hex[:8]}"
        
        message_data = {
            "message": "Hello!",
            "context": {"user_id": "test_user", "thread_id": thread_id}
        }
        response = client.post("/chatbot/chat", json=message_data)
        
        if response.status_code == 200:
            data = response.json()
            assert data["context"]["thread_id"] == thread_id
    
    def test_get_chat_history(self, client):
        """Test GET /chatbot/history returns chat history."""
        response = client.get("/chatbot/history", params={"user_id": "test_user"})
        assert response.status_code == 200
        
        data = response.json()
        assert isinstance(data, list)
    
    def test_get_chat_history_with_thread(self, client):
        """Test GET /chatbot/history with thread_id filter."""
        response = client.get(
            "/chatbot/history",
            params={"user_id": "test_user", "thread_id": "some_thread"}
        )
        assert response.status_code == 200
        
        data = response.json()
        assert isinstance(data, list)
    
    def test_get_chat_history_missing_user(self, client):
        """Test GET /chatbot/history requires user_id."""
        response = client.get("/chatbot/history")
        assert response.status_code == 422  # Validation error


# ============================================================================
# ML ENDPOINT TESTS
# ============================================================================

class TestMLEndpoints:
    """Test ML training and forecasting endpoints."""
    
    def test_train_endpoint(self, client):
        """Test POST /ml/train trains the model."""
        # This may take some time, so use longer timeout
        with httpx.Client(base_url=BASE_URL, timeout=120.0) as long_client:
            response = long_client.post("/ml/train")
            
            # 200 = success, 400 = insufficient data
            assert response.status_code in [200, 400]
            
            if response.status_code == 200:
                data = response.json()
                assert data["success"] == True
                assert "model_path" in data
                assert "training_rows" in data
    
    def test_forecast_30d(self, client):
        """Test GET /ml/forecast/30d returns 30-day forecast."""
        response = client.get("/ml/forecast/30d", params={"pricing_model": "STANDARD"})
        
        # 200 = success, 400 = model not trained
        assert response.status_code in [200, 400]
        
        if response.status_code == 200:
            data = response.json()
            assert "forecast" in data
            assert "pricing_model" in data
            assert data["days"] == 30
    
    def test_forecast_60d(self, client):
        """Test GET /ml/forecast/60d returns 60-day forecast."""
        response = client.get("/ml/forecast/60d", params={"pricing_model": "CONTRACTED"})
        
        assert response.status_code in [200, 400]
        
        if response.status_code == 200:
            data = response.json()
            assert data["days"] == 60
    
    def test_forecast_90d(self, client):
        """Test GET /ml/forecast/90d returns 90-day forecast."""
        response = client.get("/ml/forecast/90d", params={"pricing_model": "CUSTOM"})
        
        assert response.status_code in [200, 400]
        
        if response.status_code == 200:
            data = response.json()
            assert data["days"] == 90
    
    def test_forecast_invalid_pricing_model(self, client):
        """Test forecast with invalid pricing_model."""
        response = client.get("/ml/forecast/30d", params={"pricing_model": "INVALID"})
        # Should return 400 or 422
        assert response.status_code in [400, 422]


# ============================================================================
# UPLOAD ENDPOINT TESTS
# ============================================================================

class TestUploadEndpoints:
    """Test data upload endpoints."""
    
    def test_upload_historical_data_no_file(self, client):
        """Test POST /upload/historical-data without file returns error."""
        response = client.post("/upload/historical-data")
        assert response.status_code == 422  # Validation error - file required
    
    def test_upload_competitor_data_no_file(self, client):
        """Test POST /upload/competitor-data without file returns error."""
        response = client.post("/upload/competitor-data")
        assert response.status_code == 422  # Validation error - file required


# ============================================================================
# HEALTH CHECK TESTS
# ============================================================================

class TestHealthCheck:
    """Test basic API health."""
    
    def test_root_endpoint(self, client):
        """Test root endpoint returns welcome message."""
        with httpx.Client(base_url="http://localhost:8000", timeout=10.0) as root_client:
            response = root_client.get("/")
            assert response.status_code == 200
    
    def test_openapi_docs(self, client):
        """Test OpenAPI docs are accessible."""
        with httpx.Client(base_url="http://localhost:8000", timeout=10.0) as docs_client:
            response = docs_client.get("/docs")
            assert response.status_code == 200
    
    def test_openapi_json(self, client):
        """Test OpenAPI JSON schema is accessible."""
        with httpx.Client(base_url="http://localhost:8000", timeout=10.0) as schema_client:
            response = schema_client.get("/openapi.json")
            assert response.status_code == 200
            data = response.json()
            assert "openapi" in data
            assert "paths" in data


# ============================================================================
# RUN TESTS
# ============================================================================

if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])


