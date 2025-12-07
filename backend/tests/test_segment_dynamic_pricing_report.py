"""
Test Suite for Segment Dynamic Pricing Report

Tests the complete segment dynamic pricing analytics functionality including:
1. Report generation with per-segment impacts
2. API endpoints (JSON and CSV formats)
3. Chatbot tool integration
4. Data filtering and querying

LangChain Version: v1.0+
Last Verified: 2025-12-02
"""

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import pytest
import json
from unittest.mock import patch, MagicMock, Mock
from datetime import datetime, timezone

# Import specific modules instead of full app
from app.utils.report_generator import (
    generate_segment_dynamic_pricing_report,
    convert_report_to_csv
)
from app.agents.analysis import (
    get_competitor_segment_baseline,
    query_segment_dynamic_pricing_report
)


# ================================================================
# TEST 1: Report Generator - Full Report Generation
# ================================================================
@pytest.mark.asyncio
async def test_generate_segment_dynamic_pricing_report_full():
    """Test generating the complete segment dynamic pricing report."""
    # Mock MongoDB to return sample pipeline result with per_segment_impacts
    mock_pipeline_result = {
        "_id": "test_pipeline_123",
        "timestamp": datetime.now(timezone.utc),
        "per_segment_impacts": {
            "recommendation_1": [
                {
                    "segment": {
                        "location_category": "Urban",
                        "loyalty_tier": "Gold",
                        "vehicle_type": "Premium",
                        "demand_profile": "HIGH",
                        "pricing_model": "STANDARD"
                    },
                    "baseline": {"rides_30d": 100, "unit_price": 50.0, "revenue_30d": 5000.0},
                    "with_recommendation": {"rides_30d": 105, "unit_price": 52.0, "revenue_30d": 5460.0},
                    "explanation": "Applied surge pricing rule"
                }
            ],
            "recommendation_2": [],
            "recommendation_3": []
        }
    }
    
    with patch("app.utils.report_generator.get_sync_mongodb_client") as mock_client:
        mock_db = MagicMock()
        mock_client.return_value.__getitem__.return_value = mock_db
        mock_db["pipeline_results"].find_one.return_value = mock_pipeline_result
        mock_db["historical_rides"].find.return_value.limit.return_value = [
            {
                "Location_Category": "Urban",
                "Customer_Loyalty_Status": "Gold",
                "Vehicle_Type": "Premium",
                "Demand_Profile": "HIGH",
                "Pricing_Model": "STANDARD",
                "Historical_Cost_of_Ride": 48.0,
                "Historical_Ride_Distance": 10.0
            }
        ]
        mock_db["competitor_prices"].find.return_value.limit.return_value = [
            {
                "Location_Category": "Urban",
                "Customer_Loyalty_Status": "Gold",
                "Vehicle_Type": "Premium",
                "Demand_Profile": "HIGH",
                "Pricing_Model": "STANDARD",
                "Historical_Cost_of_Ride": 52.0,
                "Historical_Ride_Distance": 10.0
            }
        ]
        
        report = generate_segment_dynamic_pricing_report()
        
        assert "metadata" in report
        assert "segments" in report
        assert report["metadata"]["report_type"] == "segment_dynamic_pricing_analysis"
        assert len(report["segments"]) > 0
        
        # Check first segment structure
        segment = report["segments"][0]
        assert "segment" in segment
        assert "hwco_continue_current" in segment
        assert "lyft_continue_current" in segment
        assert "recommendation_1" in segment
        assert "recommendation_2" in segment
        assert "recommendation_3" in segment


# ================================================================
# TEST 2: Report Generator - CSV Conversion
# ================================================================
def test_convert_report_to_csv():
    """Test converting report to CSV format."""
    sample_report = {
        "metadata": {
            "report_type": "segment_dynamic_pricing_analysis",
            "generated_at": "2025-12-02T10:00:00",
            "total_segments": 1
        },
        "segments": [
            {
                "segment": {
                    "location_category": "Urban",
                    "loyalty_tier": "Gold",
                    "vehicle_type": "Premium",
                    "demand_profile": "HIGH",
                    "pricing_model": "STANDARD"
                },
                "hwco_continue_current": {
                    "rides_30d": 100,
                    "unit_price": 50.0,
                    "revenue_30d": 5000.0,
                    "explanation": "HWCO historical average"
                },
                "lyft_continue_current": {
                    "rides_30d": 95,
                    "unit_price": 52.0,
                    "revenue_30d": 4940.0,
                    "explanation": "Lyft competitor average"
                },
                "recommendation_1": {
                    "rides_30d": 105,
                    "unit_price": 52.0,
                    "revenue_30d": 5460.0,
                    "explanation": "Applied surge pricing"
                },
                "recommendation_2": {
                    "rides_30d": 102,
                    "unit_price": 51.0,
                    "revenue_30d": 5202.0,
                    "explanation": "Applied loyalty discount"
                },
                "recommendation_3": {
                    "rides_30d": 103,
                    "unit_price": 51.5,
                    "revenue_30d": 5304.5,
                    "explanation": "Applied mixed rules"
                }
            }
        ]
    }
    
    csv_content = convert_report_to_csv(sample_report)
    
    # Check CSV has headers
    assert "location_category" in csv_content
    assert "loyalty_tier" in csv_content
    assert "hwco_rides_30d" in csv_content
    assert "lyft_unit_price" in csv_content
    assert "rec1_revenue_30d" in csv_content
    
    # Check data rows
    assert "Urban" in csv_content
    assert "Gold" in csv_content
    assert "Premium" in csv_content
    
    # Check values present
    lines = csv_content.strip().split("\n")
    assert len(lines) >= 2  # Header + at least 1 data row


# ================================================================
# TEST 3: API Endpoint - JSON Format
# ================================================================
@pytest.mark.asyncio
async def test_api_segment_dynamic_pricing_json():
    """Test GET /api/v1/reports/segment-dynamic-pricing-analysis endpoint (JSON)."""
    with patch("app.utils.report_generator.generate_segment_dynamic_pricing_report") as mock_gen:
        mock_gen.return_value = {
            "metadata": {
                "report_type": "segment_dynamic_pricing_analysis",
                "generated_at": "2025-12-02T10:00:00",
                "total_segments": 1
            },
            "segments": [
                {
                    "segment": {"location_category": "Urban", "loyalty_tier": "Gold"},
                    "hwco_continue_current": {"rides_30d": 100},
                    "lyft_continue_current": {"rides_30d": 95},
                    "recommendation_1": {"rides_30d": 105},
                    "recommendation_2": {"rides_30d": 102},
                    "recommendation_3": {"rides_30d": 103}
                }
            ]
        }
        
        # Import and test the endpoint function directly
        from app.routers.reports import get_segment_dynamic_pricing_analysis
        
        response = await get_segment_dynamic_pricing_analysis(
            pipeline_result_id=None,
            format="json"
        )
        
        # Response should be JSONResponse
        assert response.status_code == 200
        data = json.loads(response.body.decode())
        assert "metadata" in data
        assert "segments" in data
        assert data["metadata"]["report_type"] == "segment_dynamic_pricing_analysis"


# ================================================================
# TEST 4: API Endpoint - CSV Format
# ================================================================
@pytest.mark.asyncio
async def test_api_segment_dynamic_pricing_csv():
    """Test GET /api/v1/reports/segment-dynamic-pricing-analysis endpoint (CSV)."""
    with patch("app.utils.report_generator.generate_segment_dynamic_pricing_report") as mock_gen, \
         patch("app.utils.report_generator.convert_report_to_csv") as mock_csv:
        mock_gen.return_value = {
            "metadata": {
                "report_type": "segment_dynamic_pricing_analysis",
                "generated_at": "2025-12-02T10:00:00",
                "total_segments": 1
            },
            "segments": []
        }
        mock_csv.return_value = "location_category,loyalty_tier\nUrban,Gold\n"
        
        # Import and test the endpoint function directly
        from app.routers.reports import get_segment_dynamic_pricing_analysis
        
        response = await get_segment_dynamic_pricing_analysis(
            pipeline_result_id=None,
            format="csv"
        )
        
        # Response should be StreamingResponse
        assert response.status_code == 200
        assert "text/csv" in response.media_type


# ================================================================
# TEST 5: Competitor Segment Baseline Tool
# ================================================================
def test_get_competitor_segment_baseline():
    """Test get_competitor_segment_baseline tool."""
    with patch("app.agents.analysis.get_sync_mongodb_client") as mock_client:
        mock_db = MagicMock()
        mock_client.return_value.__getitem__.return_value = mock_db
        mock_db["competitor_prices"].find.return_value.limit.return_value = [
            {
                "Location_Category": "Urban",
                "Customer_Loyalty_Status": "Gold",
                "Vehicle_Type": "Premium",
                "Demand_Profile": "HIGH",
                "Pricing_Model": "STANDARD",
                "Historical_Cost_of_Ride": 52.0,
                "Historical_Ride_Distance": 10.0
            },
            {
                "Location_Category": "Urban",
                "Customer_Loyalty_Status": "Gold",
                "Vehicle_Type": "Premium",
                "Demand_Profile": "HIGH",
                "Pricing_Model": "STANDARD",
                "Historical_Cost_of_Ride": 54.0,
                "Historical_Ride_Distance": 12.0
            }
        ]
        
        result = get_competitor_segment_baseline.invoke({
            "location_category": "Urban",
            "loyalty_tier": "Gold",
            "vehicle_type": "Premium",
            "demand_profile": "HIGH"
        })
        
        result_data = json.loads(result)
        assert "segment" in result_data
        assert "competitor" in result_data
        assert result_data["competitor"] == "Lyft"
        assert "baseline" in result_data
        assert result_data["baseline"]["ride_count"] == 2


# ================================================================
# TEST 6: Chatbot Tool - Query Segment Report
# ================================================================
def test_query_segment_dynamic_pricing_report_tool():
    """Test query_segment_dynamic_pricing_report chatbot tool."""
    with patch("app.utils.report_generator.generate_segment_dynamic_pricing_report") as mock_gen:
        mock_gen.return_value = {
            "metadata": {
                "report_type": "segment_dynamic_pricing_analysis",
                "generated_at": "2025-12-02T10:00:00",
                "total_segments": 2
            },
            "segments": [
                {
                    "segment": {
                        "location_category": "Urban",
                        "loyalty_tier": "Gold",
                        "vehicle_type": "Premium",
                        "demand_profile": "HIGH",
                        "pricing_model": "STANDARD"
                    },
                    "hwco_continue_current": {"rides_30d": 100},
                    "lyft_continue_current": {"rides_30d": 95},
                    "recommendation_1": {"rides_30d": 105},
                    "recommendation_2": {"rides_30d": 102},
                    "recommendation_3": {"rides_30d": 103}
                },
                {
                    "segment": {
                        "location_category": "Suburban",
                        "loyalty_tier": "Silver",
                        "vehicle_type": "Economy",
                        "demand_profile": "MEDIUM",
                        "pricing_model": "STANDARD"
                    },
                    "hwco_continue_current": {"rides_30d": 150},
                    "lyft_continue_current": {"rides_30d": 145},
                    "recommendation_1": {"rides_30d": 155},
                    "recommendation_2": {"rides_30d": 152},
                    "recommendation_3": {"rides_30d": 153}
                }
            ]
        }
        
        # Test without filter (all segments)
        result = query_segment_dynamic_pricing_report.invoke({})
        result_data = json.loads(result)
        assert "segments_returned" in result_data
        assert result_data["segments_returned"] == 2
        
        # Test with filter (Urban only)
        result = query_segment_dynamic_pricing_report.invoke({"location_category": "Urban"})
        result_data = json.loads(result)
        assert result_data["segments_returned"] == 1
        assert result_data["segments"][0]["segment"]["location_category"] == "Urban"


# ================================================================
# TEST 7: API Endpoint - Summary Endpoint
# ================================================================
@pytest.mark.asyncio
async def test_api_segment_dynamic_pricing_summary():
    """Test GET /api/v1/reports/segment-dynamic-pricing-analysis/summary endpoint."""
    mock_report = {
        "metadata": {
            "report_type": "segment_dynamic_pricing_analysis",
            "generated_at": "2025-12-02T10:00:00",
            "total_segments": 1
        },
        "segments": [
            {
                "segment": {"location_category": "Urban"},
                "hwco_continue_current": {"rides_30d": 100, "unit_price": 50.0, "revenue_30d": 5000.0},
                "lyft_continue_current": {"rides_30d": 95, "unit_price": 52.0, "revenue_30d": 4940.0},
                "recommendation_1": {"rides_30d": 105, "unit_price": 52.0, "revenue_30d": 5460.0},
                "recommendation_2": {"rides_30d": 102, "unit_price": 51.0, "revenue_30d": 5202.0},
                "recommendation_3": {"rides_30d": 103, "unit_price": 51.5, "revenue_30d": 5304.5}
            }
        ]
    }
    
    with patch("app.routers.reports.generate_segment_dynamic_pricing_report") as mock_gen:
        mock_gen.return_value = mock_report
        
        # Import and test the endpoint function directly
        from app.routers.reports import get_segment_dynamic_pricing_summary
        
        response = await get_segment_dynamic_pricing_summary(pipeline_result_id=None)
        
        assert response.status_code == 200
        data = json.loads(response.body.decode())
        assert "metadata" in data
        assert "aggregate_revenue_30d" in data
        assert "revenue_uplift" in data
        assert data["aggregate_revenue_30d"]["hwco_continue_current"] == 5000.0
        assert "rec1_vs_hwco_pct" in data["revenue_uplift"]
        # Calculate expected uplift: (5460 - 5000) / 5000 * 100 = 9.2%
        assert abs(data["revenue_uplift"]["rec1_vs_hwco_pct"] - 9.2) < 0.1


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

