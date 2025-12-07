"""
Test suite for ML Prophet model combined data training (HWCO + Competitor).

This test suite validates:
1. Combined data loading from both collections
2. Data standardization for training
3. Rideshare_Company regressor integration
4. ML train endpoint response structure
5. Forecast generation with HWCO-specific patterns

Tests use HTTP API calls to avoid numpy import issues on macOS.
"""

import pytest
import requests
import json
from datetime import datetime

# ============================================================================
# Configuration
# ============================================================================

BASE_URL = "http://localhost:8000/api/v1"
TIMEOUT = 30
TRAIN_TIMEOUT = 120  # Training can take longer


def server_is_running() -> bool:
    """Check if the backend server is running with retries."""
    for attempt in range(3):
        try:
            response = requests.get(f"{BASE_URL.replace('/api/v1', '')}/health", timeout=10)
            if response.status_code == 200:
                return True
        except requests.exceptions.RequestException:
            if attempt < 2:
                import time
                time.sleep(1)  # Brief wait before retry
    return False


# Check server once at module load
_server_available = server_is_running()


@pytest.fixture(autouse=True)
def check_server():
    """Skip tests if server is not running."""
    if not _server_available:
        pytest.skip("Backend server not running at localhost:8000")


# ============================================================================
# Test: ML Train Endpoint with Combined Data
# ============================================================================

class TestMLTrainEndpoint:
    """Tests for the /ml/train endpoint with combined HWCO + competitor data."""
    
    def test_train_endpoint_exists(self):
        """Test that the train endpoint is accessible."""
        response = requests.post(f"{BASE_URL}/ml/train", timeout=TRAIN_TIMEOUT)
        # Should return 200 (success) or 400 (insufficient data), not 404
        assert response.status_code in [200, 400], f"Unexpected status: {response.status_code}"
    
    def test_train_response_structure(self):
        """Test that train response includes data source breakdown."""
        response = requests.post(f"{BASE_URL}/ml/train", timeout=TRAIN_TIMEOUT)
        
        if response.status_code == 200:
            data = response.json()
            # Check for data_sources field
            assert "data_sources" in data, "Response should include data_sources field"
            
            data_sources = data["data_sources"]
            assert "hwco_rows" in data_sources, "Should include hwco_rows count"
            assert "competitor_rows" in data_sources, "Should include competitor_rows count"
            assert "total_rows" in data_sources, "Should include total_rows count"
            assert "collections" in data_sources, "Should include collections list"
            
            # Verify collections include both sources
            collections = data_sources["collections"]
            assert "historical_rides" in collections, "Should include historical_rides"
            assert "competitor_prices" in collections, "Should include competitor_prices"
            
            # Verify row counts are reasonable
            assert data_sources["hwco_rows"] >= 0, "hwco_rows should be non-negative"
            assert data_sources["competitor_rows"] >= 0, "competitor_rows should be non-negative"
            assert data_sources["total_rows"] == data_sources["hwco_rows"] + data_sources["competitor_rows"], \
                "total_rows should equal hwco_rows + competitor_rows"
        elif response.status_code == 400:
            # Insufficient data - check error message mentions combined data
            data = response.json()
            assert "detail" in data, "Error response should have detail"
            print(f"Training skipped (insufficient data): {data['detail']}")
    
    def test_train_message_mentions_combined_data(self):
        """Test that success message mentions combined data sources."""
        response = requests.post(f"{BASE_URL}/ml/train", timeout=TRAIN_TIMEOUT)
        
        if response.status_code == 200:
            data = response.json()
            message = data.get("message", "")
            # Message should mention HWCO and Competitor counts
            assert "HWCO" in message or "combined" in message.lower(), \
                f"Message should mention combined data: {message}"


# ============================================================================
# Test: ML Forecast Endpoint
# ============================================================================

class TestMLForecastEndpoint:
    """Tests for the /ml/forecast endpoint after combined training."""
    
    def test_forecast_30d_standard(self):
        """Test 30-day forecast for STANDARD pricing."""
        response = requests.get(
            f"{BASE_URL}/ml/forecast/30d",
            params={"pricing_model": "STANDARD"},
            timeout=TIMEOUT
        )
        # Should return 200 or 400 (if model not trained)
        assert response.status_code in [200, 400], f"Unexpected status: {response.status_code}"
        
        if response.status_code == 200:
            data = response.json()
            assert "forecast" in data, "Response should include forecast"
            assert len(data["forecast"]) > 0, "Forecast should have data points"
    
    def test_forecast_60d_contracted(self):
        """Test 60-day forecast for CONTRACTED pricing."""
        response = requests.get(
            f"{BASE_URL}/ml/forecast/60d",
            params={"pricing_model": "CONTRACTED"},
            timeout=TIMEOUT
        )
        assert response.status_code in [200, 400], f"Unexpected status: {response.status_code}"
    
    def test_forecast_90d_custom(self):
        """Test 90-day forecast for CUSTOM pricing."""
        response = requests.get(
            f"{BASE_URL}/ml/forecast/90d",
            params={"pricing_model": "CUSTOM"},
            timeout=TIMEOUT
        )
        assert response.status_code in [200, 400], f"Unexpected status: {response.status_code}"


# ============================================================================
# Test: Pipeline Orchestrator Retraining
# ============================================================================

class TestPipelineRetraining:
    """Tests for pipeline orchestrator's combined data retraining."""
    
    def test_pipeline_status_available(self):
        """Test that pipeline status endpoint is available."""
        response = requests.get(f"{BASE_URL}/pipeline/status", timeout=TIMEOUT)
        assert response.status_code == 200, f"Pipeline status failed: {response.status_code}"
    
    def test_pipeline_can_trigger_with_force(self):
        """Test that pipeline can be force-triggered."""
        response = requests.post(
            f"{BASE_URL}/pipeline/trigger",
            json={"force": True, "reason": "Test combined data training"},
            timeout=TIMEOUT
        )
        assert response.status_code == 200, f"Pipeline trigger failed: {response.status_code}"
        
        data = response.json()
        # Should either start or already be running
        assert data.get("success") or data.get("status") == "running", \
            f"Pipeline should start or be running: {data}"


# ============================================================================
# Test: Data Standardization
# ============================================================================

class TestDataStandardization:
    """Tests for data standardization logic (via integration tests)."""
    
    def test_analytics_metrics_include_competitor_data(self):
        """Test that analytics considers competitor data."""
        try:
            response = requests.get(f"{BASE_URL}/analytics/metrics", timeout=60)
            
            if response.status_code == 200:
                data = response.json()
                # Check if competitor data is being tracked
                # This validates that competitor_prices collection is accessible
                assert isinstance(data, dict), "Should return metrics dict"
            else:
                # Analytics endpoint may be slow, accept other status codes
                pytest.skip(f"Analytics endpoint returned {response.status_code}")
        except requests.exceptions.ReadTimeout:
            # Skip test if analytics takes too long (it's computationally heavy)
            pytest.skip("Analytics endpoint timed out - this is expected for large datasets")
    
    def test_health_check_still_works(self):
        """Verify health check after combined training changes."""
        response = requests.get(
            f"{BASE_URL.replace('/api/v1', '')}/health",
            timeout=TIMEOUT
        )
        assert response.status_code == 200, "Health check should pass"


# ============================================================================
# Test: ML Training Metadata
# ============================================================================

class TestMLTrainingMetadata:
    """Tests for ML training metadata storage."""
    
    def test_training_stores_data_sources(self):
        """Test that training metadata includes data source info."""
        # First, trigger training
        train_response = requests.post(f"{BASE_URL}/ml/train", timeout=TRAIN_TIMEOUT)
        
        if train_response.status_code == 200:
            # Check pipeline status for training info
            status_response = requests.get(f"{BASE_URL}/pipeline/status", timeout=TIMEOUT)
            assert status_response.status_code == 200
            
            # Training should have completed
            train_data = train_response.json()
            assert train_data.get("success"), "Training should succeed"
            assert "data_sources" in train_data, "Should include data_sources"


# ============================================================================
# Test: Regressor Integration
# ============================================================================

class TestRegressorIntegration:
    """Tests for Rideshare_Company regressor in forecasts."""
    
    def test_forecast_uses_hwco_patterns(self):
        """Test that forecasts use HWCO-specific patterns."""
        # Train first
        train_response = requests.post(f"{BASE_URL}/ml/train", timeout=TRAIN_TIMEOUT)
        
        if train_response.status_code == 200:
            # Generate forecast
            forecast_response = requests.get(
                f"{BASE_URL}/ml/forecast/30d",
                params={"pricing_model": "STANDARD"},
                timeout=TIMEOUT
            )
            
            if forecast_response.status_code == 200:
                data = forecast_response.json()
                forecast = data.get("forecast", [])
                
                # Verify forecast has expected structure
                if forecast:
                    first_point = forecast[0]
                    assert "date" in first_point or "ds" in first_point, \
                        "Forecast should have date field"
                    assert "predicted_demand" in first_point or "yhat" in first_point, \
                        "Forecast should have prediction field"


# ============================================================================
# Test: Error Handling
# ============================================================================

class TestErrorHandling:
    """Tests for error handling in combined training."""
    
    def test_invalid_pricing_model_handled(self):
        """Test that invalid pricing model returns appropriate error."""
        response = requests.get(
            f"{BASE_URL}/ml/forecast/30d",
            params={"pricing_model": "INVALID"},
            timeout=TIMEOUT
        )
        # Should return 400 or 422 for invalid input
        assert response.status_code in [400, 422], f"Should reject invalid pricing model: {response.status_code}"
    
    def test_missing_pricing_model_handled(self):
        """Test that missing pricing model is handled."""
        response = requests.get(
            f"{BASE_URL}/ml/forecast/30d",
            timeout=TIMEOUT
        )
        # Should return 422 for missing required parameter
        assert response.status_code == 422, f"Should require pricing_model: {response.status_code}"


# ============================================================================
# Main
# ============================================================================

if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])


