"""
Reports Router - Segment Dynamic Pricing Analysis

Provides API endpoints for generating and retrieving segment-level dynamic pricing reports
containing historical baselines, competitor baselines, and forecast data for all recommendations.

Supports both JSON and CSV output formats.
"""

from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import StreamingResponse, JSONResponse
from typing import Optional, Dict, Any
from datetime import datetime, timedelta
import io
import logging

from app.models.schemas import (
    SegmentDynamicPricingReport,
    SegmentDynamicPricingReportRequest
)
from app.utils.report_generator import (
    generate_segment_dynamic_pricing_report,
    convert_report_to_csv
)

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/reports",
    tags=["reports"],
    responses={404: {"description": "Not found"}}
)

# ============================================================================
# SERVER-SIDE CACHE (to speed up repeated requests)
# ============================================================================
_report_cache: Dict[str, Any] = {}
_cache_timestamp: Dict[str, datetime] = {}
CACHE_DURATION_MINUTES = 30  # Cache reports for 30 minutes


@router.get(
    "/segment-dynamic-pricing-analysis",
    summary="Get Segment Dynamic Pricing Analysis Report",
    description="""
    Generate comprehensive segment dynamic pricing report for all 162 segments.
    
    Each segment includes:
    - HWCO Continue Current: Historical baseline (rides, unit_price, revenue, explanation)
    - Lyft Continue Current: Competitor baseline (rides, unit_price, revenue, explanation)
    - Recommendation 1: Forecasted metrics with rules applied
    - Recommendation 2: Forecasted metrics with rules applied
    - Recommendation 3: Forecasted metrics with rules applied
    
    Supports both JSON and CSV output formats via the 'format' query parameter.
    """
)
async def get_segment_dynamic_pricing_analysis(
    pipeline_result_id: Optional[str] = Query(
        default=None,
        description="Specific pipeline result ID (optional, uses latest if not provided)"
    ),
    format: str = Query(
        default="json",
        description="Output format: 'json' or 'csv'",
        pattern="^(json|csv)$"
    )
):
    """
    Get segment dynamic pricing analysis report.
    
    Query Parameters:
    - pipeline_result_id: Optional ID of specific pipeline result to use (defaults to latest)
    - format: Output format - 'json' (default) or 'csv'
    
    Returns:
    - JSON: SegmentDynamicPricingReport with metadata and segment data
    - CSV: Downloadable CSV file with all segment data in tabular format
    """
    try:
        # Create cache key
        cache_key = pipeline_result_id or "latest"
        
        # Check cache first
        if cache_key in _report_cache and cache_key in _cache_timestamp:
            cache_age = datetime.utcnow() - _cache_timestamp[cache_key]
            if cache_age < timedelta(minutes=CACHE_DURATION_MINUTES):
                logger.info(f"✅ Using cached report (age: {cache_age.total_seconds():.1f}s)")
                report = _report_cache[cache_key]
                
                # Return based on requested format
                if format.lower() == "csv":
                    csv_content = convert_report_to_csv(report)
                    return StreamingResponse(
                        iter([csv_content]),
                        media_type="text/csv",
                        headers={
                            "Content-Disposition": f"attachment; filename=segment_dynamic_pricing_report_{report['metadata']['generated_at']}.csv"
                        }
                    )
                else:
                    return JSONResponse(content=report)
        
        # Cache miss or expired - generate fresh report
        logger.info(f"🔄 Generating fresh report (cache miss or expired)")
        
        # Generate the report
        report = generate_segment_dynamic_pricing_report(pipeline_result_id)
        
        # Check for errors
        if "error" in report:
            raise HTTPException(
                status_code=404,
                detail=report.get("error", "Error generating report")
            )
        
        # Cache the report
        _report_cache[cache_key] = report
        _cache_timestamp[cache_key] = datetime.utcnow()
        logger.info(f"💾 Report cached for {CACHE_DURATION_MINUTES} minutes")
        
        # Return based on requested format
        if format.lower() == "csv":
            # Convert to CSV
            csv_content = convert_report_to_csv(report)
            
            # Create streaming response
            csv_buffer = io.StringIO(csv_content)
            
            return StreamingResponse(
                iter([csv_content]),
                media_type="text/csv",
                headers={
                    "Content-Disposition": f"attachment; filename=segment_dynamic_pricing_report_{report['metadata']['generated_at']}.csv"
                }
            )
        else:
            # Return JSON (default)
            return JSONResponse(content=report)
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error generating segment dynamic pricing report: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Error generating report: {str(e)}"
        )


@router.get(
    "/segment-dynamic-pricing-analysis/summary",
    summary="Get Report Summary",
    description="Get summary statistics for the latest segment dynamic pricing analysis"
)
async def get_segment_dynamic_pricing_summary(
    pipeline_result_id: Optional[str] = Query(
        default=None,
        description="Specific pipeline result ID (optional, uses latest if not provided)"
    )
):
    """
    Get summary statistics for segment dynamic pricing analysis.
    
    Returns only metadata without the full segment-level data (for quick overview).
    """
    try:
        # Generate the report
        report = generate_segment_dynamic_pricing_report(pipeline_result_id)
        
        # Check for errors
        if "error" in report:
            raise HTTPException(
                status_code=404,
                detail=report.get("error", "Error generating report")
            )
        
        # Return only metadata and aggregate stats
        segments = report.get("segments", [])
        
        # Calculate aggregate statistics
        total_hwco_revenue = sum(
            seg.get("hwco_continue_current", {}).get("revenue_30d", 0)
            for seg in segments
        )
        total_lyft_revenue = sum(
            seg.get("lyft_continue_current", {}).get("revenue_30d", 0)
            for seg in segments
        )
        total_rec1_revenue = sum(
            seg.get("recommendation_1", {}).get("revenue_30d", 0)
            for seg in segments
        )
        total_rec2_revenue = sum(
            seg.get("recommendation_2", {}).get("revenue_30d", 0)
            for seg in segments
        )
        total_rec3_revenue = sum(
            seg.get("recommendation_3", {}).get("revenue_30d", 0)
            for seg in segments
        )
        
        summary = {
            "metadata": report.get("metadata", {}),
            "aggregate_revenue_30d": {
                "hwco_continue_current": round(total_hwco_revenue, 2),
                "lyft_continue_current": round(total_lyft_revenue, 2),
                "recommendation_1": round(total_rec1_revenue, 2),
                "recommendation_2": round(total_rec2_revenue, 2),
                "recommendation_3": round(total_rec3_revenue, 2)
            },
            "revenue_uplift": {
                "rec1_vs_hwco_pct": round(
                    ((total_rec1_revenue - total_hwco_revenue) / total_hwco_revenue * 100)
                    if total_hwco_revenue > 0 else 0,
                    2
                ),
                "rec2_vs_hwco_pct": round(
                    ((total_rec2_revenue - total_hwco_revenue) / total_hwco_revenue * 100)
                    if total_hwco_revenue > 0 else 0,
                    2
                ),
                "rec3_vs_hwco_pct": round(
                    ((total_rec3_revenue - total_hwco_revenue) / total_hwco_revenue * 100)
                    if total_hwco_revenue > 0 else 0,
                    2
                )
            }
        }
        
        return JSONResponse(content=summary)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error generating report summary: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Error generating summary: {str(e)}"
        )

