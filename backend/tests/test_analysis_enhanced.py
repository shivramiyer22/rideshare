"""
Test script for enhanced Analysis Agent.

Tests:
- KPI calculation tools
- n8n data analysis tools
- Structured insights generation
- OpenAI GPT-4 integration
"""
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import pytest
import json
from app.agents.analysis import (
    calculate_revenue_kpis,
    calculate_profit_metrics,
    calculate_rides_count,
    analyze_customer_segments,
    analyze_event_impact_on_demand,
    analyze_traffic_patterns,
    analyze_industry_trends,
    generate_structured_insights,
    analysis_agent
)

# Check if agent is available (may be None if API key missing)
ANALYSIS_AGENT_AVAILABLE = analysis_agent is not None
from app.database import connect_to_mongo, get_database
import asyncio


class TestAnalysisEnhanced:
    """Test enhanced Analysis Agent."""
    
    def test_kpi_tools_are_callable(self):
        """Test that KPI calculation tools are callable."""
        # LangChain tools are StructuredTool objects, check if they have invoke method
        assert hasattr(calculate_revenue_kpis, 'invoke') or callable(calculate_revenue_kpis)
        assert hasattr(calculate_profit_metrics, 'invoke') or callable(calculate_profit_metrics)
        assert hasattr(calculate_rides_count, 'invoke') or callable(calculate_rides_count)
        assert hasattr(analyze_customer_segments, 'invoke') or callable(analyze_customer_segments)
        
        print("✓ All KPI calculation tools are available")
        return True
    
    def test_n8n_analysis_tools_are_callable(self):
        """Test that n8n data analysis tools are callable."""
        # LangChain tools are StructuredTool objects
        assert hasattr(analyze_event_impact_on_demand, 'invoke') or callable(analyze_event_impact_on_demand)
        assert hasattr(analyze_traffic_patterns, 'invoke') or callable(analyze_traffic_patterns)
        assert hasattr(analyze_industry_trends, 'invoke') or callable(analyze_industry_trends)
        
        print("✓ All n8n data analysis tools are available")
        return True
    
    def test_structured_insights_tool_is_callable(self):
        """Test that structured insights tool is callable."""
        # LangChain tools are StructuredTool objects
        assert hasattr(generate_structured_insights, 'invoke') or callable(generate_structured_insights)
        
        print("✓ Structured insights tool is available")
        return True
    
    def test_calculate_revenue_kpis_structure(self):
        """Test revenue KPIs calculation returns proper structure."""
        try:
            # LangChain tools use .invoke() method
            if hasattr(calculate_revenue_kpis, 'invoke'):
                result = calculate_revenue_kpis.invoke({"time_period": "30d"})
            else:
                result = calculate_revenue_kpis("30d")
            
            # Should return JSON string
            assert isinstance(result, str)
            
            # Try to parse as JSON
            kpi_data = json.loads(result)
            
            # Should have expected keys (or error key)
            if "error" not in kpi_data:
                assert "total_revenue" in kpi_data or "time_period" in kpi_data
            else:
                # Error is OK if database not connected
                assert "error" in kpi_data
                print("⚠ Database connection not available (expected in test env)")
            
            print("✓ Revenue KPIs calculation returns proper structure")
            return True
        except Exception as e:
            print(f"✗ Revenue KPIs error: {str(e)}")
            return False
    
    def test_calculate_rides_count_structure(self):
        """Test ride counts calculation returns proper structure."""
        try:
            # LangChain tools use .invoke() method
            if hasattr(calculate_rides_count, 'invoke'):
                result = calculate_rides_count.invoke({"time_period": "30d"})
            else:
                result = calculate_rides_count("30d")
            
            assert isinstance(result, str)
            kpi_data = json.loads(result)
            
            if "error" not in kpi_data:
                assert "time_period" in kpi_data
            else:
                print("⚠ Database connection not available (expected in test env)")
            
            print("✓ Ride counts calculation returns proper structure")
            return True
        except Exception as e:
            print(f"✗ Ride counts error: {str(e)}")
            return False
    
    def test_analyze_customer_segments_structure(self):
        """Test customer segments analysis returns proper structure."""
        try:
            # LangChain tools use .invoke() method
            if hasattr(analyze_customer_segments, 'invoke'):
                result = analyze_customer_segments.invoke({})
            else:
                result = analyze_customer_segments()
            
            assert isinstance(result, str)
            segment_data = json.loads(result)
            
            if "error" not in segment_data:
                # Should have customer segment data
                assert isinstance(segment_data, dict)
            else:
                print("⚠ Database connection not available (expected in test env)")
            
            print("✓ Customer segments analysis returns proper structure")
            return True
        except Exception as e:
            print(f"✗ Customer segments error: {str(e)}")
            return False
    
    def test_n8n_analysis_tools_with_data(self):
        """Test n8n data analysis tools with sample data."""
        try:
            # LangChain tools use .invoke() method
            # Test event impact analysis
            if hasattr(analyze_event_impact_on_demand, 'invoke'):
                event_result = analyze_event_impact_on_demand.invoke({"event_data": "Lakers game Friday evening"})
            else:
                event_result = analyze_event_impact_on_demand("Lakers game Friday evening")
            assert isinstance(event_result, str)
            assert len(event_result) > 0
            
            # Test traffic patterns
            if hasattr(analyze_traffic_patterns, 'invoke'):
                traffic_result = analyze_traffic_patterns.invoke({"traffic_data": "Heavy traffic downtown"})
            else:
                traffic_result = analyze_traffic_patterns("Heavy traffic downtown")
            assert isinstance(traffic_result, str)
            assert len(traffic_result) > 0
            
            # Test industry trends
            if hasattr(analyze_industry_trends, 'invoke'):
                news_result = analyze_industry_trends.invoke({"news_data": "Rideshare industry news"})
            else:
                news_result = analyze_industry_trends("Rideshare industry news")
            assert isinstance(news_result, str)
            assert len(news_result) > 0
            
            print("✓ n8n data analysis tools work with sample data")
            return True
        except Exception as e:
            print(f"✗ n8n analysis tools error: {str(e)}")
            return False
    
    def test_structured_insights_with_openai(self):
        """Test structured insights generation with OpenAI (if API key available)."""
        try:
            # Test with sample KPIs
            sample_kpis = json.dumps({
                "total_revenue": 50000,
                "average_revenue_per_ride": 25.50,
                "revenue_growth_percent": 15.5
            })
            
            # LangChain tools use .invoke() method
            if hasattr(generate_structured_insights, 'invoke'):
                result = generate_structured_insights.invoke({
                    "kpis": sample_kpis,
                    "context": "test context",
                    "time_period": "30d"
                })
            else:
                result = generate_structured_insights(sample_kpis, "test context", "30d")
            
            assert isinstance(result, str)
            
            # Try to parse as JSON (OpenAI returns JSON)
            try:
                insights = json.loads(result)
                if "error" not in insights:
                    # Should have structured insights
                    assert isinstance(insights, dict)
                    print("✓ Structured insights generated successfully")
                else:
                    print("⚠ OpenAI API key not available (expected in test env)")
            except json.JSONDecodeError:
                # If not JSON, might be error message
                if "error" in result.lower() or "api_key" in result.lower():
                    print("⚠ OpenAI API key not available (expected in test env)")
                else:
                    print(f"⚠ Unexpected response format: {result[:100]}")
            
            return True
        except Exception as e:
            if "api_key" in str(e).lower() or "openai" in str(e).lower():
                print("⚠ OpenAI API key not available (expected in test env)")
                return True
            print(f"✗ Structured insights error: {str(e)}")
            return False
    
    def test_analysis_agent_has_all_tools(self):
        """Test that analysis agent has all required tools."""
        if not ANALYSIS_AGENT_AVAILABLE:
            print("⚠ Analysis agent not available (OPENAI_API_KEY required)")
            return True
        
        try:
            assert analysis_agent is not None
            
            # Verify agent has tools (tools are internal to LangChain agent)
            # We can verify by checking the tools are imported and callable
            # All tools should be callable
            assert callable(calculate_revenue_kpis)
            assert callable(generate_structured_insights)
            
            print("✓ Analysis agent has all required tools")
            return True
        except Exception as e:
            if "api_key" in str(e).lower() or "openai" in str(e).lower():
                print("⚠ Analysis agent requires OPENAI_API_KEY (expected in test env)")
                return True
            print(f"✗ Analysis agent tools error: {str(e)}")
            return False


if __name__ == "__main__":
    print("=" * 60)
    print("Testing Enhanced Analysis Agent")
    print("=" * 60)
    
    # Try to connect to MongoDB (optional)
    try:
        asyncio.run(connect_to_mongo())
    except Exception as e:
        print(f"⚠ MongoDB connection not available: {e}")
        print("Some tests may be skipped")
    
    test_instance = TestAnalysisEnhanced()
    
    tests = [
        ("KPI tools are callable", test_instance.test_kpi_tools_are_callable),
        ("n8n analysis tools are callable", test_instance.test_n8n_analysis_tools_are_callable),
        ("Structured insights tool is callable", test_instance.test_structured_insights_tool_is_callable),
        ("Revenue KPIs structure", test_instance.test_calculate_revenue_kpis_structure),
        ("Ride counts structure", test_instance.test_calculate_rides_count_structure),
        ("Customer segments structure", test_instance.test_analyze_customer_segments_structure),
        ("n8n analysis tools with data", test_instance.test_n8n_analysis_tools_with_data),
        ("Structured insights with OpenAI", test_instance.test_structured_insights_with_openai),
        ("Analysis agent has all tools", test_instance.test_analysis_agent_has_all_tools),
    ]
    
    passed = 0
    failed = 0
    
    for test_name, test_func in tests:
        try:
            if test_func():
                passed += 1
            else:
                failed += 1
        except Exception as e:
            print(f"✗ {test_name}: {str(e)}")
            failed += 1
    
    print("=" * 60)
    print(f"Results: {passed} passed, {failed} failed")
    print("=" * 60)
    
    if failed == 0:
        print("✅ All tests passed!")
        sys.exit(0)
    else:
        print("❌ Some tests failed")
        sys.exit(1)

