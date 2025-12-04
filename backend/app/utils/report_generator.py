"""
Report Generator for Segment Dynamic Pricing Analysis

This module generates comprehensive reports for all 162 segments containing:
1. Historical baseline (HWCO Continue Current)
2. Competitor baseline (Lyft Continue Current)
3. Forecast data for each of the 3 recommendations

LangChain Version: v1.0+
Documentation Reference: https://docs.langchain.com/oss/python/langchain
Last Verified: 2025-12-02
"""

import json
import csv
from io import StringIO
from typing import Dict, Any, List
from datetime import datetime, timezone
import pymongo
from app.config import settings
import logging

logger = logging.getLogger(__name__)


def get_sync_mongodb_client():
    """Get a synchronous MongoDB client."""
    return pymongo.MongoClient(settings.mongodb_url)


def generate_segment_dynamic_pricing_report(pipeline_result_id: str = None) -> Dict[str, Any]:
    """
    Generate comprehensive segment dynamic pricing report for all 162 segments.
    
    For each segment, the report includes:
    1. Segment dimensions (location_category, loyalty_tier, vehicle_type, demand_profile, pricing_model)
    2. HWCO Continue Current: Historical baseline (rides, unit_price, revenue, explanation)
    3. Lyft Continue Current: Competitor baseline (rides, unit_price, revenue, explanation)
    4. Recommendation 1: Forecasted metrics with rules applied (rides, unit_price, revenue, explanation)
    5. Recommendation 2: Forecasted metrics with rules applied (rides, unit_price, revenue, explanation)
    6. Recommendation 3: Forecasted metrics with rules applied (rides, unit_price, revenue, explanation)
    
    Args:
        pipeline_result_id: Specific pipeline result ID to use (optional, uses latest if None)
    
    Returns:
        Dict containing report metadata and segment-level data for all 162 segments
    """
    try:
        client = get_sync_mongodb_client()
        db = client[settings.mongodb_db_name]
        
        # Get the pipeline result (latest or specific)
        pipeline_collection = db["pipeline_results"]
        if pipeline_result_id:
            pipeline_result = pipeline_collection.find_one({"_id": pipeline_result_id})
        else:
            # Get most recent pipeline result by completed_at
            pipeline_result = pipeline_collection.find_one(
                sort=[("completed_at", pymongo.DESCENDING)]
            )
        
        if not pipeline_result:
            return {
                "error": "No pipeline results found",
                "segments": []
            }
        
        # Extract per-segment impacts from pipeline result
        per_segment_impacts = pipeline_result.get("per_segment_impacts", {})
        rec1_impacts = per_segment_impacts.get("recommendation_1", [])
        rec2_impacts = per_segment_impacts.get("recommendation_2", [])
        rec3_impacts = per_segment_impacts.get("recommendation_3", [])
        
        # Get historical baseline data from historical_rides
        historical_collection = db["historical_rides"]
        competitor_collection = db["competitor_prices"]
        
        # Build report for all segments
        report_segments = []
        
        # Iterate through all recommendation 1 impacts (which should cover all 162 segments)
        for rec1_impact in rec1_impacts:
            segment_dims = rec1_impact.get("segment", {})
            
            # Find matching impacts in rec2 and rec3
            rec2_impact = next(
                (r for r in rec2_impacts if r.get("segment") == segment_dims),
                None
            )
            rec3_impact = next(
                (r for r in rec3_impacts if r.get("segment") == segment_dims),
                None
            )
            
            # Get HWCO historical baseline
            hwco_query = {
                "Location_Category": segment_dims.get("location_category"),
                "Customer_Loyalty_Status": segment_dims.get("loyalty_tier"),
                "Vehicle_Type": segment_dims.get("vehicle_type"),
                "Demand_Profile": segment_dims.get("demand_profile"),
                "Pricing_Model": segment_dims.get("pricing_model", "STANDARD")
            }
            hwco_rides = list(historical_collection.find(hwco_query).limit(1000))
            
            if hwco_rides:
                # Calculate using NEW data model: duration and unit_price
                hwco_avg_duration = sum(r.get("Expected_Ride_Duration", 0) for r in hwco_rides) / len(hwco_rides)
                hwco_avg_unit_price = sum(r.get("Historical_Unit_Price", 0) for r in hwco_rides) / len(hwco_rides)
                hwco_ride_count = len(hwco_rides)
                # Revenue = rides × duration × unit_price
                hwco_revenue = hwco_ride_count * hwco_avg_duration * hwco_avg_unit_price
                hwco_explanation = f"HWCO historical average: {hwco_ride_count} rides, ${hwco_avg_unit_price:.2f}/min, {hwco_avg_duration:.1f} min avg, ${hwco_revenue:.2f} revenue"
            else:
                hwco_avg_unit_price = 0
                hwco_ride_count = 0
                hwco_revenue = 0
                hwco_explanation = "No HWCO historical data for this segment"
            
            # Get Lyft competitor baseline
            lyft_query = hwco_query.copy()
            lyft_rides = list(competitor_collection.find(lyft_query).limit(1000))
            
            if lyft_rides:
                # Calculate using NEW data model: duration and unit_price
                lyft_avg_duration = sum(r.get("Expected_Ride_Duration", 0) for r in lyft_rides) / len(lyft_rides)
                lyft_avg_unit_price = sum(r.get("unit_price", 0) for r in lyft_rides) / len(lyft_rides)
                lyft_ride_count = len(lyft_rides)
                # Revenue = rides × duration × unit_price
                lyft_revenue = lyft_ride_count * lyft_avg_duration * lyft_avg_unit_price
                lyft_explanation = f"Lyft competitor average: {lyft_ride_count} rides, ${lyft_avg_unit_price:.2f}/min, {lyft_avg_duration:.1f} min avg, ${lyft_revenue:.2f} revenue"
            else:
                lyft_avg_unit_price = 0
                lyft_ride_count = 0
                lyft_revenue = 0
                lyft_explanation = "No Lyft competitor data for this segment"
            
            # Build segment report row
            segment_report = {
                "segment": segment_dims,
                "hwco_continue_current": {
                    "rides_30d": hwco_ride_count,
                    "unit_price": round(hwco_avg_unit_price, 2),
                    "revenue_30d": round(hwco_revenue, 2),
                    "explanation": hwco_explanation
                },
                "lyft_continue_current": {
                    "rides_30d": lyft_ride_count,
                    "unit_price": round(lyft_avg_unit_price, 2),
                    "revenue_30d": round(lyft_revenue, 2),
                    "explanation": lyft_explanation
                },
                "recommendation_1": {
                    "rides_30d": rec1_impact.get("with_recommendation", {}).get("rides_30d", 0),
                    "unit_price": rec1_impact.get("with_recommendation", {}).get("unit_price", 0),
                    "revenue_30d": rec1_impact.get("with_recommendation", {}).get("revenue_30d", 0),
                    "explanation": rec1_impact.get("explanation", "No rules applied")
                } if rec1_impact else {
                    "rides_30d": 0,
                    "unit_price": 0,
                    "revenue_30d": 0,
                    "explanation": "No forecast data"
                },
                "recommendation_2": {
                    "rides_30d": rec2_impact.get("with_recommendation", {}).get("rides_30d", 0),
                    "unit_price": rec2_impact.get("with_recommendation", {}).get("unit_price", 0),
                    "revenue_30d": rec2_impact.get("with_recommendation", {}).get("revenue_30d", 0),
                    "explanation": rec2_impact.get("explanation", "No rules applied")
                } if rec2_impact else {
                    "rides_30d": 0,
                    "unit_price": 0,
                    "revenue_30d": 0,
                    "explanation": "No forecast data"
                },
                "recommendation_3": {
                    "rides_30d": rec3_impact.get("with_recommendation", {}).get("rides_30d", 0),
                    "unit_price": rec3_impact.get("with_recommendation", {}).get("unit_price", 0),
                    "revenue_30d": rec3_impact.get("with_recommendation", {}).get("revenue_30d", 0),
                    "explanation": rec3_impact.get("explanation", "No rules applied")
                } if rec3_impact else {
                    "rides_30d": 0,
                    "unit_price": 0,
                    "revenue_30d": 0,
                    "explanation": "No forecast data"
                }
            }
            
            report_segments.append(segment_report)
        
        # Build final report
        report = {
            "metadata": {
                "report_type": "segment_dynamic_pricing_analysis",
                "generated_at": datetime.now(timezone.utc).isoformat(),
                "pipeline_result_id": str(pipeline_result.get("_id", "")),
                "pipeline_timestamp": pipeline_result.get("timestamp", ""),
                "total_segments": len(report_segments),
                "dimensions": ["location_category", "loyalty_tier", "vehicle_type", "demand_profile", "pricing_model"]
            },
            "segments": report_segments
        }
        
        client.close()
        return report
        
    except Exception as e:
        logger.error(f"Error generating segment dynamic pricing report: {e}")
        return {
            "error": f"Error generating report: {str(e)}",
            "segments": []
        }


def convert_report_to_csv(report: Dict[str, Any]) -> str:
    """
    Convert segment dynamic pricing report to CSV format.
    
    CSV columns:
    - Segment dimensions (5 columns)
    - HWCO Continue Current (4 columns: rides, price, revenue, explanation)
    - Lyft Continue Current (4 columns: rides, price, revenue, explanation)
    - Recommendation 1 (4 columns: rides, price, revenue, explanation)
    - Recommendation 2 (4 columns: rides, price, revenue, explanation)
    - Recommendation 3 (4 columns: rides, price, revenue, explanation)
    Total: 5 + 4*5 = 25 columns
    
    Args:
        report: Report dictionary from generate_segment_dynamic_pricing_report()
    
    Returns:
        CSV string
    """
    try:
        segments = report.get("segments", [])
        if not segments:
            return "No data available"
        
        # Build CSV in memory
        output = StringIO()
        
        # Define column headers
        fieldnames = [
            # Segment dimensions
            "location_category",
            "loyalty_tier",
            "vehicle_type",
            "demand_profile",
            "pricing_model",
            # HWCO Continue Current
            "hwco_rides_30d",
            "hwco_unit_price",
            "hwco_revenue_30d",
            "hwco_explanation",
            # Lyft Continue Current
            "lyft_rides_30d",
            "lyft_unit_price",
            "lyft_revenue_30d",
            "lyft_explanation",
            # Recommendation 1
            "rec1_rides_30d",
            "rec1_unit_price",
            "rec1_revenue_30d",
            "rec1_explanation",
            # Recommendation 2
            "rec2_rides_30d",
            "rec2_unit_price",
            "rec2_revenue_30d",
            "rec2_explanation",
            # Recommendation 3
            "rec3_rides_30d",
            "rec3_unit_price",
            "rec3_revenue_30d",
            "rec3_explanation"
        ]
        
        writer = csv.DictWriter(output, fieldnames=fieldnames)
        writer.writeheader()
        
        # Write data rows
        for segment_data in segments:
            segment_dims = segment_data.get("segment", {})
            hwco = segment_data.get("hwco_continue_current", {})
            lyft = segment_data.get("lyft_continue_current", {})
            rec1 = segment_data.get("recommendation_1", {})
            rec2 = segment_data.get("recommendation_2", {})
            rec3 = segment_data.get("recommendation_3", {})
            
            row = {
                # Segment dimensions
                "location_category": segment_dims.get("location_category", ""),
                "loyalty_tier": segment_dims.get("loyalty_tier", ""),
                "vehicle_type": segment_dims.get("vehicle_type", ""),
                "demand_profile": segment_dims.get("demand_profile", ""),
                "pricing_model": segment_dims.get("pricing_model", "STANDARD"),
                # HWCO Continue Current
                "hwco_rides_30d": hwco.get("rides_30d", 0),
                "hwco_unit_price": hwco.get("unit_price", 0),
                "hwco_revenue_30d": hwco.get("revenue_30d", 0),
                "hwco_explanation": hwco.get("explanation", ""),
                # Lyft Continue Current
                "lyft_rides_30d": lyft.get("rides_30d", 0),
                "lyft_unit_price": lyft.get("unit_price", 0),
                "lyft_revenue_30d": lyft.get("revenue_30d", 0),
                "lyft_explanation": lyft.get("explanation", ""),
                # Recommendation 1
                "rec1_rides_30d": rec1.get("rides_30d", 0),
                "rec1_unit_price": rec1.get("unit_price", 0),
                "rec1_revenue_30d": rec1.get("revenue_30d", 0),
                "rec1_explanation": rec1.get("explanation", ""),
                # Recommendation 2
                "rec2_rides_30d": rec2.get("rides_30d", 0),
                "rec2_unit_price": rec2.get("unit_price", 0),
                "rec2_revenue_30d": rec2.get("revenue_30d", 0),
                "rec2_explanation": rec2.get("explanation", ""),
                # Recommendation 3
                "rec3_rides_30d": rec3.get("rides_30d", 0),
                "rec3_unit_price": rec3.get("unit_price", 0),
                "rec3_revenue_30d": rec3.get("revenue_30d", 0),
                "rec3_explanation": rec3.get("explanation", "")
            }
            
            writer.writerow(row)
        
        csv_content = output.getvalue()
        output.close()
        
        return csv_content
        
    except Exception as e:
        logger.error(f"Error converting report to CSV: {e}")
        return f"Error generating CSV: {str(e)}"
