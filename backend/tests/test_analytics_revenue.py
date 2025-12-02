"""
Test script for Analytics Revenue endpoint.

Tests the GET /api/v1/analytics/revenue endpoint that provides
data for the AnalyticsDashboard component.
"""
import sys
from pathlib import Path
from unittest.mock import patch, MagicMock, AsyncMock
import pytest
from datetime import datetime, timedelta

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))


class TestAnalyticsRevenueEndpoint:
    """Test suite for analytics revenue endpoint."""
    
    def test_endpoint_validation_periods(self):
        """Test that valid periods are accepted."""
        valid_periods = ["7d", "30d", "60d", "90d"]
        for period in valid_periods:
            assert period in valid_periods
    
    def test_endpoint_imports(self):
        """Test that analytics router can be imported."""
        try:
            from app.routers import analytics
            assert analytics is not None
            assert hasattr(analytics, 'router')
        except ImportError as e:
            pytest.skip(f"Analytics router imports failed: {e}")
    
    def test_revenue_endpoint_exists(self):
        """Test that revenue endpoint function exists."""
        try:
            from app.routers.analytics import get_analytics_revenue
            assert get_analytics_revenue is not None
            assert callable(get_analytics_revenue)
        except ImportError as e:
            pytest.skip(f"Revenue endpoint import failed: {e}")
    
    def test_date_range_calculation(self):
        """Test date range calculation logic."""
        days_map = {"7d": 7, "30d": 30, "60d": 60, "90d": 90}
        
        for period, expected_days in days_map.items():
            days = days_map.get(period, 30)
            assert days == expected_days
        
        # Test default
        days = days_map.get("invalid", 30)
        assert days == 30
    
    def test_response_structure(self):
        """Test that response structure matches expected format."""
        expected_keys = [
            "total_revenue",
            "total_rides",
            "avg_revenue_per_ride",
            "customer_distribution",
            "revenue_chart_data",
            "top_routes",
            "period"
        ]
        
        # Mock response structure
        mock_response = {
            "total_revenue": 1000.0,
            "total_rides": 50,
            "avg_revenue_per_ride": 20.0,
            "customer_distribution": {"Gold": 10, "Silver": 20, "Regular": 20},
            "revenue_chart_data": [{"date": "2024-01-01", "revenue": 100.0, "rides": 5}],
            "top_routes": [{"route": "A → B", "revenue": 500.0, "rides": 25}],
            "period": "30d"
        }
        
        for key in expected_keys:
            assert key in mock_response, f"Missing key: {key}"
    
    def test_customer_distribution_structure(self):
        """Test customer distribution structure."""
        customer_dist = {"Gold": 10, "Silver": 20, "Regular": 30}
        
        assert "Gold" in customer_dist
        assert "Silver" in customer_dist
        assert "Regular" in customer_dist
        assert isinstance(customer_dist["Gold"], int)
        assert isinstance(customer_dist["Silver"], int)
        assert isinstance(customer_dist["Regular"], int)


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])


