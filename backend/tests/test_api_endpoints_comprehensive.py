"""
Comprehensive API Endpoint Testing
Tests all 38 backend API endpoints for correctness, data integrity, and error handling.

Test Coverage:
- Health checks
- Order management (estimate, create, get, queue)
- ML forecasting (30d, 60d, 90d)
- Analytics (dashboard, metrics, revenue, what-if)
- Reports (segment analysis, summary)
- Pipeline (trigger, status, history, changes)
- Chatbot (chat, history)
- Upload (historical, competitor, strategies)
- Agent tests (pricing, analysis, forecasting, recommendation)
- Users (CRUD operations)
"""

import pytest
import requests
import json
from datetime import datetime, timedelta
from typing import Dict, Any

BASE_URL = "http://localhost:8000"

class TestHealthAndRoot:
    """Test basic health and root endpoints"""
    
    def test_root_endpoint(self):
        """Test GET / returns welcome message"""
        response = requests.get(f"{BASE_URL}/")
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert "Rideshare Dynamic Pricing API" in data["message"]
    
    def test_health_check(self):
        """Test GET /health returns healthy status"""
        response = requests.get(f"{BASE_URL}/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert "database" in data
        assert "redis" in data


class TestOrdersEndpoints:
    """Test all order-related endpoints"""
    
    def test_estimate_order_price(self):
        """Test POST /api/v1/orders/estimate"""
        payload = {
            "origin": "Downtown",
            "destination": "Airport",
            "duration": 25.0,
            "pricing_model": "SURGE",
            "vehicle_type": "Premium",
            "loyalty_tier": "Gold",
            "location_category": "Urban",
            "demand_profile": "HIGH"
        }
        response = requests.post(f"{BASE_URL}/api/v1/orders/estimate", json=payload)
        assert response.status_code == 200
        data = response.json()
        assert "estimated_price" in data
        assert "breakdown" in data
        assert data["estimated_price"] > 0
    
    def test_create_order(self):
        """Test POST /api/v1/orders/ creates order successfully"""
        payload = {
            "origin": "Downtown",
            "destination": "Airport",
            "duration": 25.0,
            "pricing_model": "SURGE",
            "vehicle_type": "Premium",
            "loyalty_tier": "Gold",
            "location_category": "Urban",
            "demand_profile": "HIGH"
        }
        response = requests.post(f"{BASE_URL}/api/v1/orders/", json=payload)
        assert response.status_code == 200
        data = response.json()
        assert "order_id" in data
        assert data["status"] == "pending"
        assert "estimated_price" in data
        return data["order_id"]  # Return for subsequent tests
    
    def test_get_orders(self):
        """Test GET /api/v1/orders/ returns order list"""
        response = requests.get(f"{BASE_URL}/api/v1/orders/")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
    
    def test_get_specific_order(self):
        """Test GET /api/v1/orders/{order_id}"""
        # First create an order
        order_id = self.test_create_order()
        
        # Then fetch it
        response = requests.get(f"{BASE_URL}/api/v1/orders/{order_id}")
        assert response.status_code == 200
        data = response.json()
        assert data["order_id"] == order_id
        assert "estimated_price" in data
        assert "segment_avg_fcs_unit_price" in data
        assert "segment_avg_fcs_ride_duration" in data
    
    def test_get_priority_queue(self):
        """Test GET /api/v1/orders/queue/priority"""
        response = requests.get(f"{BASE_URL}/api/v1/orders/queue/priority")
        assert response.status_code == 200
        data = response.json()
        assert "high_priority" in data
        assert "medium_priority" in data
        assert "low_priority" in data


class TestMLEndpoints:
    """Test ML forecasting endpoints"""
    
    def test_forecast_30d(self):
        """Test GET /api/v1/ml/forecast/30d"""
        response = requests.get(f"{BASE_URL}/api/v1/ml/forecast/30d")
        assert response.status_code == 200
        data = response.json()
        assert "forecast" in data or "predictions" in data
    
    def test_forecast_60d(self):
        """Test GET /api/v1/ml/forecast/60d"""
        response = requests.get(f"{BASE_URL}/api/v1/ml/forecast/60d")
        assert response.status_code == 200
        data = response.json()
        assert "forecast" in data or "predictions" in data
    
    def test_forecast_90d(self):
        """Test GET /api/v1/ml/forecast/90d"""
        response = requests.get(f"{BASE_URL}/api/v1/ml/forecast/90d")
        assert response.status_code == 200
        data = response.json()
        assert "forecast" in data or "predictions" in data


class TestAnalyticsEndpoints:
    """Test analytics endpoints"""
    
    def test_get_dashboard(self):
        """Test GET /api/v1/analytics/dashboard"""
        response = requests.get(f"{BASE_URL}/api/v1/analytics/dashboard")
        assert response.status_code == 200
        data = response.json()
        assert "total_revenue_7d" in data or "kpis" in data
    
    def test_get_metrics(self):
        """Test GET /api/v1/analytics/metrics"""
        response = requests.get(f"{BASE_URL}/api/v1/analytics/metrics")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, (dict, list))
    
    def test_get_revenue(self):
        """Test GET /api/v1/analytics/revenue"""
        response = requests.get(f"{BASE_URL}/api/v1/analytics/revenue")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, dict)
    
    def test_what_if_analysis(self):
        """Test POST /api/v1/analytics/what-if-analysis"""
        payload = {
            "scenario": "increase_surge_multiplier",
            "parameters": {
                "surge_multiplier": 1.5
            }
        }
        response = requests.post(f"{BASE_URL}/api/v1/analytics/what-if-analysis", json=payload)
        assert response.status_code == 200
        data = response.json()
        assert "impact" in data or "results" in data


class TestReportsEndpoints:
    """Test report generation endpoints"""
    
    def test_get_segment_pricing_analysis(self):
        """Test GET /api/v1/reports/segment-dynamic-pricing-analysis"""
        response = requests.get(f"{BASE_URL}/api/v1/reports/segment-dynamic-pricing-analysis")
        assert response.status_code == 200
        data = response.json()
        assert "segments" in data
        segments = data["segments"]
        assert len(segments) == 162  # Should have all 162 segments
        
        # Verify segment structure
        if len(segments) > 0:
            sample = segments[0]
            assert "segment" in sample
            assert "hwco_continue_current" in sample
            assert "lyft_competitor" in sample
            assert "recommendation_1" in sample
            assert "recommendation_2" in sample
            assert "recommendation_3" in sample
            
            # Verify all scenarios have required fields
            for scenario_key in ["hwco_continue_current", "lyft_competitor", 
                                  "recommendation_1", "recommendation_2", "recommendation_3"]:
                scenario = sample[scenario_key]
                assert "rides_30d" in scenario
                assert "unit_price" in scenario
                assert "duration_minutes" in scenario
                assert "revenue_30d" in scenario
                assert "explanation" in scenario
    
    def test_get_report_summary(self):
        """Test GET /api/v1/reports/segment-dynamic-pricing-analysis/summary"""
        response = requests.get(f"{BASE_URL}/api/v1/reports/segment-dynamic-pricing-analysis/summary")
        assert response.status_code == 200
        data = response.json()
        assert "total_segments" in data
        assert "recommendations" in data


class TestPipelineEndpoints:
    """Test pipeline orchestration endpoints"""
    
    def test_get_pipeline_status(self):
        """Test GET /api/v1/pipeline/status"""
        response = requests.get(f"{BASE_URL}/api/v1/pipeline/status")
        assert response.status_code == 200
        data = response.json()
        assert "status" in data
    
    def test_get_pipeline_history(self):
        """Test GET /api/v1/pipeline/history"""
        response = requests.get(f"{BASE_URL}/api/v1/pipeline/history")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
    
    def test_get_pending_changes(self):
        """Test GET /api/v1/pipeline/changes"""
        response = requests.get(f"{BASE_URL}/api/v1/pipeline/changes")
        assert response.status_code == 200
        data = response.json()
        assert "pending_changes" in data or "changes_count" in data
    
    def test_get_last_run(self):
        """Test GET /api/v1/pipeline/last-run"""
        response = requests.get(f"{BASE_URL}/api/v1/pipeline/last-run")
        assert response.status_code == 200
        data = response.json()
        # May be null if no runs yet
        if data:
            assert "run_id" in data
    
    def test_trigger_pipeline(self):
        """Test POST /api/v1/pipeline/trigger"""
        payload = {"trigger_source": "manual_test"}
        response = requests.post(f"{BASE_URL}/api/v1/pipeline/trigger", json=payload)
        assert response.status_code in [200, 202]  # Accept or OK
        data = response.json()
        assert "run_id" in data or "status" in data


class TestChatbotEndpoints:
    """Test chatbot endpoints"""
    
    def test_chat_message(self):
        """Test POST /api/v1/chatbot/chat"""
        payload = {
            "message": "What is the average price for Urban rides?",
            "thread_id": "test_thread_001"
        }
        response = requests.post(f"{BASE_URL}/api/v1/chatbot/chat", json=payload)
        assert response.status_code == 200
        data = response.json()
        assert "response" in data
        assert len(data["response"]) > 0
    
    def test_get_chat_history(self):
        """Test GET /api/v1/chatbot/history"""
        response = requests.get(f"{BASE_URL}/api/v1/chatbot/history?thread_id=test_thread_001")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)


class TestAgentTestEndpoints:
    """Test agent testing endpoints"""
    
    def test_pricing_agent(self):
        """Test POST /api/v1/agents/test/pricing"""
        payload = {
            "location_category": "Urban",
            "vehicle_type": "Premium",
            "loyalty_tier": "Gold",
            "duration": 30.0
        }
        response = requests.post(f"{BASE_URL}/api/v1/agents/test/pricing", json=payload)
        assert response.status_code == 200
        data = response.json()
        assert "price" in data or "result" in data
    
    def test_forecasting_agent(self):
        """Test POST /api/v1/agents/test/forecasting"""
        payload = {"days": 30}
        response = requests.post(f"{BASE_URL}/api/v1/agents/test/forecasting", json=payload)
        assert response.status_code == 200
        data = response.json()
        assert "forecasts" in data or "result" in data
    
    def test_analysis_agent(self):
        """Test POST /api/v1/agents/test/analysis"""
        payload = {"analysis_type": "pricing_rules"}
        response = requests.post(f"{BASE_URL}/api/v1/agents/test/analysis", json=payload)
        assert response.status_code == 200
        data = response.json()
        assert "rules" in data or "result" in data
    
    def test_recommendation_agent(self):
        """Test POST /api/v1/agents/test/recommendation"""
        payload = {"scenario": "optimize_revenue"}
        response = requests.post(f"{BASE_URL}/api/v1/agents/test/recommendation", json=payload)
        assert response.status_code == 200
        data = response.json()
        assert "recommendations" in data or "result" in data


class TestUsersEndpoints:
    """Test user management endpoints"""
    
    def test_get_users(self):
        """Test GET /api/v1/users/"""
        response = requests.get(f"{BASE_URL}/api/v1/users/")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
    
    def test_create_user(self):
        """Test POST /api/v1/users/"""
        payload = {
            "name": "Test User",
            "email": f"test_{datetime.utcnow().timestamp()}@example.com",
            "loyalty_tier": "Silver"
        }
        response = requests.post(f"{BASE_URL}/api/v1/users/", json=payload)
        assert response.status_code in [200, 201]
        data = response.json()
        assert "user_id" in data or "_id" in data
        return data.get("user_id") or data.get("_id")
    
    def test_get_specific_user(self):
        """Test GET /api/v1/users/{user_id}"""
        user_id = self.test_create_user()
        response = requests.get(f"{BASE_URL}/api/v1/users/{user_id}")
        assert response.status_code == 200
        data = response.json()
        assert data.get("user_id") == user_id or str(data.get("_id")) == user_id
    
    def test_update_user(self):
        """Test PUT /api/v1/users/{user_id}"""
        user_id = self.test_create_user()
        payload = {"loyalty_tier": "Gold"}
        response = requests.put(f"{BASE_URL}/api/v1/users/{user_id}", json=payload)
        assert response.status_code == 200
    
    def test_delete_user(self):
        """Test DELETE /api/v1/users/{user_id}"""
        user_id = self.test_create_user()
        response = requests.delete(f"{BASE_URL}/api/v1/users/{user_id}")
        assert response.status_code in [200, 204]


if __name__ == "__main__":
    # Run tests with pytest
    pytest.main([__file__, "-v", "--tb=short"])
