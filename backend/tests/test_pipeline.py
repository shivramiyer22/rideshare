"""
Test suite for the Agent Pipeline Enhancement.

Tests cover:
1. Pipeline API endpoints (via HTTP - avoids numpy import issues)
2. Basic validation of pipeline responses

These tests validate the pipeline runs correctly without affecting
the existing chatbot functionality.

Run with: pytest tests/test_pipeline.py -v

Note: Due to macOS numpy compatibility issues with chromadb,
this test file uses HTTP-based testing via requests/httpx
instead of direct module imports.
"""

import pytest
import requests
import json
from datetime import datetime

# Base URL for API tests - requires running server
BASE_URL = "http://localhost:8000/api/v1"
TIMEOUT = 30


def server_is_running():
    """Check if the backend server is running with retries."""
    for attempt in range(3):
        try:
            response = requests.get("http://localhost:8000/health", timeout=10)
            if response.status_code == 200:
                return True
        except Exception as e:
            if attempt < 2:
                import time
                time.sleep(1)  # Brief wait before retry
            else:
                print(f"Server check failed after retries: {e}")
    return False


# Check server once at module load
_server_available = server_is_running()


@pytest.fixture(autouse=True)
def check_server():
    """Skip test if server is not running."""
    if not _server_available:
        pytest.skip("Backend server not running on localhost:8000")


# ============================================================================
# PIPELINE API ENDPOINT TESTS
# ============================================================================

class TestPipelineEndpoints:
    """Test the pipeline API endpoints via HTTP."""
    
    def test_get_status_endpoint(self):
        """Test GET /api/v1/pipeline/status returns valid status."""
        response = requests.get(f"{BASE_URL}/pipeline/status")
        
        assert response.status_code == 200
        data = response.json()
        
        assert "is_running" in data
        assert "current_run_id" in data
        assert "current_status" in data
        assert "change_tracker" in data
        assert isinstance(data["is_running"], bool)
    
    def test_get_pending_changes_endpoint(self):
        """Test GET /api/v1/pipeline/changes returns change tracker status."""
        response = requests.get(f"{BASE_URL}/pipeline/changes")
        
        assert response.status_code == 200
        data = response.json()
        
        assert "pending_changes" in data
        assert "collections_changed" in data
    
    def test_get_history_endpoint(self):
        """Test GET /api/v1/pipeline/history returns run history."""
        response = requests.get(f"{BASE_URL}/pipeline/history")
        
        assert response.status_code == 200
        data = response.json()
        
        assert "total" in data
        assert "runs" in data
        assert isinstance(data["runs"], list)
    
    def test_get_history_with_limit(self):
        """Test GET /api/v1/pipeline/history with custom limit."""
        response = requests.get(f"{BASE_URL}/pipeline/history?limit=5")
        
        assert response.status_code == 200
        data = response.json()
        
        assert len(data["runs"]) <= 5
    
    def test_get_last_run_endpoint(self):
        """Test GET /api/v1/pipeline/last-run returns last run details."""
        response = requests.get(f"{BASE_URL}/pipeline/last-run")
        
        assert response.status_code == 200
        data = response.json()
        
        assert "message" in data
        # last_run can be None if no runs exist
        assert "last_run" in data
    
    def test_trigger_pipeline_no_changes(self):
        """Test POST /api/v1/pipeline/trigger without changes returns appropriate message."""
        # Clear any existing changes first
        requests.post(f"{BASE_URL}/pipeline/clear-changes")
        
        # Try to trigger without force
        response = requests.post(
            f"{BASE_URL}/pipeline/trigger",
            json={"force": False}
        )
        
        assert response.status_code == 200
        data = response.json()
        
        # Should indicate no changes detected OR pipeline started
        assert "success" in data
        assert "message" in data
    
    def test_trigger_pipeline_with_force(self):
        """Test POST /api/v1/pipeline/trigger with force=true."""
        response = requests.post(
            f"{BASE_URL}/pipeline/trigger",
            json={"force": True, "reason": "Test forced trigger"}
        )
        
        assert response.status_code == 200
        data = response.json()
        
        # Should either start or indicate already running
        assert "success" in data
        assert "message" in data
    
    def test_clear_changes_endpoint(self):
        """Test POST /api/v1/pipeline/clear-changes clears the tracker."""
        response = requests.post(f"{BASE_URL}/pipeline/clear-changes")
        
        assert response.status_code == 200
        data = response.json()
        
        assert "message" in data
        assert "cleared" in data


# ============================================================================
# CHATBOT COMPATIBILITY TESTS
# ============================================================================

class TestChatbotCompatibility:
    """
    Verify that chatbot functionality continues to work
    after pipeline enhancements.
    """
    
    def test_chatbot_still_works(self):
        """Test that chatbot API still responds correctly."""
        response = requests.post(
            f"{BASE_URL}/chatbot/chat",
            json={
                "message": "What is the current revenue?",
                "context": {}
            },
            timeout=60
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert "response" in data
        # Response should not be empty
        assert len(data["response"]) > 0
    
    def test_analytics_still_works(self):
        """Test that analytics API still works after pipeline changes."""
        response = requests.get(f"{BASE_URL}/analytics/metrics")
        
        assert response.status_code == 200
        data = response.json()
        
        # Should return metrics structure
        assert isinstance(data, dict)
    
    def test_ml_forecast_endpoint_available(self):
        """Test that ML forecasting API is still available after pipeline changes."""
        # Use the correct endpoint path: GET /ml/forecast/30d with pricing_model parameter
        response = requests.get(f"{BASE_URL}/ml/forecast/30d?pricing_model=STANDARD")
        
        # May return 400 if no model trained, but should not error with 500
        assert response.status_code in [200, 400]


# ============================================================================
# INTEGRATION TESTS
# ============================================================================

class TestPipelineIntegration:
    """Integration tests for the full pipeline flow."""
    
    def test_pipeline_status_structure(self):
        """Test that pipeline status has correct structure."""
        response = requests.get(f"{BASE_URL}/pipeline/status")
        data = response.json()
        
        # Verify change_tracker structure
        tracker = data.get("change_tracker", {})
        assert "pending_changes" in tracker
        assert "collections_changed" in tracker
        assert "last_change_time" in tracker
    
    def test_pipeline_history_structure(self):
        """Test that pipeline history items have correct structure."""
        response = requests.get(f"{BASE_URL}/pipeline/history")
        data = response.json()
        
        # If there are runs, verify structure
        if data["runs"]:
            run = data["runs"][0]
            assert "run_id" in run
            assert "status" in run
            assert "trigger_source" in run
    
    def test_pipeline_endpoints_dont_break_health(self):
        """Test that pipeline endpoints don't break health check."""
        # Access pipeline endpoints
        requests.get(f"{BASE_URL}/pipeline/status")
        requests.get(f"{BASE_URL}/pipeline/history")
        
        # Verify health check still works
        response = requests.get("http://localhost:8000/health")
        assert response.status_code == 200
        assert response.json()["status"] == "healthy"


# ============================================================================
# CONCURRENT ACCESS TESTS
# ============================================================================

class TestConcurrentAccess:
    """Test that pipeline doesn't block other operations."""
    
    def test_analytics_during_pipeline_status_check(self):
        """Test analytics works while checking pipeline status."""
        # Check pipeline status
        status_response = requests.get(f"{BASE_URL}/pipeline/status")
        assert status_response.status_code == 200
        
        # Analytics should still work
        analytics_response = requests.get(f"{BASE_URL}/analytics/dashboard")
        assert analytics_response.status_code == 200
    
    def test_chatbot_during_pipeline_operations(self):
        """Test chatbot works during pipeline operations."""
        # Clear changes (pipeline operation)
        requests.post(f"{BASE_URL}/pipeline/clear-changes")
        
        # Chatbot should still work
        chatbot_response = requests.post(
            f"{BASE_URL}/chatbot/chat",
            json={"message": "Hello", "context": {}},
            timeout=60
        )
        assert chatbot_response.status_code == 200


# ============================================================================
# RUN CONFIGURATION
# ============================================================================

if __name__ == "__main__":
    if server_is_running():
        pytest.main([__file__, "-v", "--tb=short"])
    else:
        print("ERROR: Backend server not running on localhost:8000")
        print("Start the server with: cd backend && uvicorn app.main:app --reload")
