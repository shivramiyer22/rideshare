"""
Pipeline Orchestrator - Coordinates agent pipeline execution.

This module orchestrates the execution of multiple agents in response to
MongoDB data changes. The pipeline runs:

1. PARALLEL PHASE: Forecasting Agent + Analysis Agent (competitor, external, pricing rules)
2. SEQUENTIAL: Recommendation Agent (uses outputs from phase 1)
3. SEQUENTIAL: What-If Impact Analysis (uses recommendations)

The pipeline can be triggered:
- Automatically: Hourly scheduler (only if changes detected)
- Manually: Via API endpoint POST /api/v1/pipeline/trigger

Results are stored in MongoDB `pipeline_results` collection.

IMPORTANT: This pipeline runs independently of chatbot queries.
All existing chatbot functionality continues to work unchanged.
"""

import asyncio
import logging
from datetime import datetime
from typing import Dict, Any, Optional, List, Tuple
from uuid import uuid4
import json

from app.config import settings
from app.database import get_database

logger = logging.getLogger(__name__)


class PipelineStatus:
    """Pipeline run status constants."""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    PARTIAL = "partial"  # Some phases completed, some failed


class AgentPipeline:
    """
    Orchestrates the agent pipeline execution.
    
    Pipeline Phases:
    1. Forecasting Phase (parallel with Analysis)
    2. Analysis Phase (parallel with Forecasting)
       - Competitor analysis
       - External data analysis (news, events, traffic)
       - Dynamic pricing rules generation
    3. Recommendation Phase (sequential - uses phase 1 & 2 outputs)
    4. What-If Impact Phase (sequential - uses recommendations)
    """
    
    def __init__(self):
        self.current_run_id: Optional[str] = None
        self.current_status: str = PipelineStatus.PENDING
        self._is_running: bool = False
    
    def is_running(self) -> bool:
        """Check if a pipeline is currently running."""
        return self._is_running
    
    def generate_run_id(self) -> str:
        """Generate a unique pipeline run ID."""
        timestamp = datetime.utcnow().strftime("%Y%m%d-%H%M%S")
        return f"PIPE-{timestamp}-{uuid4().hex[:6]}"
    
    async def run(
        self,
        trigger_source: str,
        changes_summary: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Execute the full agent pipeline.
        
        Args:
            trigger_source: "scheduled_hourly" or "manual_api"
            changes_summary: Summary of MongoDB changes that triggered this run
            
        Returns:
            Dict with pipeline results and metadata
        """
        if self._is_running:
            logger.warning("Pipeline already running, skipping new run request")
            return {
                "success": False,
                "error": "Pipeline already running",
                "current_run_id": self.current_run_id
            }
        
        self._is_running = True
        self.current_run_id = self.generate_run_id()
        self.current_status = PipelineStatus.RUNNING
        
        run_record = {
            "run_id": self.current_run_id,
            "trigger_source": trigger_source,
            "started_at": datetime.utcnow(),
            "completed_at": None,
            "status": PipelineStatus.RUNNING,
            "changes_processed": changes_summary or {},
            "phases": {},
            "results": {},
            "errors": []
        }
        
        logger.info("=" * 60)
        logger.info(f"Pipeline Run Started: {self.current_run_id}")
        logger.info(f"Trigger: {trigger_source}")
        if changes_summary:
            logger.info(f"Changes: {changes_summary.get('change_count', 0)} from {len(changes_summary.get('collections_changed', []))} collections")
        logger.info("=" * 60)
        
        try:
            # Save initial run record
            await self._save_run_record(run_record)
            
            # ================================================================
            # PHASE 1 & 2: PARALLEL - Forecasting + Analysis
            # ================================================================
            logger.info("\n[PHASE 1 & 2] Running Forecasting and Analysis in PARALLEL...")
            
            forecasting_task = asyncio.create_task(
                self._run_forecasting_phase()
            )
            analysis_task = asyncio.create_task(
                self._run_analysis_phase()
            )
            
            # Wait for both to complete
            forecasting_result, analysis_result = await asyncio.gather(
                forecasting_task,
                analysis_task,
                return_exceptions=True
            )
            
            # Handle exceptions from parallel tasks
            if isinstance(forecasting_result, Exception):
                logger.error(f"Forecasting phase failed: {forecasting_result}")
                run_record["errors"].append(f"Forecasting: {str(forecasting_result)}")
                forecasting_result = {"success": False, "error": str(forecasting_result)}
            
            if isinstance(analysis_result, Exception):
                logger.error(f"Analysis phase failed: {analysis_result}")
                run_record["errors"].append(f"Analysis: {str(analysis_result)}")
                analysis_result = {"success": False, "error": str(analysis_result)}
            
            run_record["phases"]["forecasting"] = forecasting_result
            run_record["phases"]["analysis"] = analysis_result
            run_record["results"]["forecasting"] = forecasting_result.get("data", {})
            run_record["results"]["analysis"] = analysis_result.get("data", {})
            
            logger.info(f"  Forecasting: {'✓' if forecasting_result.get('success') else '✗'}")
            logger.info(f"  Analysis: {'✓' if analysis_result.get('success') else '✗'}")
            
            # ================================================================
            # PHASE 3: SEQUENTIAL - Recommendations
            # ================================================================
            logger.info("\n[PHASE 3] Running Recommendation Phase...")
            
            # Combine context from phase 1 & 2 for recommendations
            recommendation_context = {
                "forecasting": forecasting_result.get("data", {}),
                "analysis": analysis_result.get("data", {})
            }
            
            try:
                recommendation_result = await self._run_recommendation_phase(recommendation_context)
            except Exception as e:
                logger.error(f"Recommendation phase failed: {e}")
                run_record["errors"].append(f"Recommendation: {str(e)}")
                recommendation_result = {"success": False, "error": str(e)}
            
            run_record["phases"]["recommendation"] = recommendation_result
            run_record["results"]["recommendations"] = recommendation_result.get("data", {})
            logger.info(f"  Recommendations: {'✓' if recommendation_result.get('success') else '✗'}")
            
            # ================================================================
            # PHASE 4: SEQUENTIAL - What-If Impact Analysis
            # ================================================================
            logger.info("\n[PHASE 4] Running What-If Impact Analysis...")
            
            try:
                whatif_result = await self._run_whatif_phase(recommendation_result.get("data", {}))
            except Exception as e:
                logger.error(f"What-If phase failed: {e}")
                run_record["errors"].append(f"What-If: {str(e)}")
                whatif_result = {"success": False, "error": str(e)}
            
            run_record["phases"]["whatif"] = whatif_result
            run_record["results"]["whatif_impact"] = whatif_result.get("data", {})
            logger.info(f"  What-If Impact: {'✓' if whatif_result.get('success') else '✗'}")
            
            # ================================================================
            # FINALIZE
            # ================================================================
            run_record["completed_at"] = datetime.utcnow()
            
            # Determine overall status
            all_success = all([
                forecasting_result.get("success", False),
                analysis_result.get("success", False),
                recommendation_result.get("success", False),
                whatif_result.get("success", False)
            ])
            
            if all_success:
                run_record["status"] = PipelineStatus.COMPLETED
            elif run_record["errors"]:
                run_record["status"] = PipelineStatus.PARTIAL
            else:
                run_record["status"] = PipelineStatus.COMPLETED
            
            # Save final run record
            await self._save_run_record(run_record)
            
            duration = (run_record["completed_at"] - run_record["started_at"]).total_seconds()
            logger.info("\n" + "=" * 60)
            logger.info(f"Pipeline Run Completed: {self.current_run_id}")
            logger.info(f"Status: {run_record['status']}")
            logger.info(f"Duration: {duration:.2f} seconds")
            if run_record["errors"]:
                logger.info(f"Errors: {len(run_record['errors'])}")
            logger.info("=" * 60)
            
            self.current_status = run_record["status"]
            return {
                "success": run_record["status"] in [PipelineStatus.COMPLETED, PipelineStatus.PARTIAL],
                "run_id": self.current_run_id,
                "status": run_record["status"],
                "duration_seconds": duration,
                "results": run_record["results"],
                "errors": run_record["errors"]
            }
            
        except Exception as e:
            logger.error(f"Pipeline run failed with exception: {e}")
            run_record["status"] = PipelineStatus.FAILED
            run_record["completed_at"] = datetime.utcnow()
            run_record["errors"].append(str(e))
            await self._save_run_record(run_record)
            
            self.current_status = PipelineStatus.FAILED
            return {
                "success": False,
                "run_id": self.current_run_id,
                "status": PipelineStatus.FAILED,
                "error": str(e)
            }
        finally:
            self._is_running = False
    
    async def _run_forecasting_phase(self) -> Dict[str, Any]:
        """
        Run the Forecasting Agent to generate fresh forecasts WITH EXPLANATIONS.
        
        IMPORTANT: First checks if historical/competitor data has changed and
        retrains the Prophet ML model if needed BEFORE generating forecasts.
        
        Uses the existing Forecasting Agent tools to generate
        30-day, 60-day, and 90-day forecasts for all pricing models,
        then generates natural language explanations for each.
        """
        logger.info("    → Running Forecasting Agent...")
        
        try:
            from app.agents.forecasting import generate_prophet_forecast, explain_forecast, query_event_context
            
            forecasts = {}
            explanations = {}
            model_retrained = False
            retraining_result = None
            
            # ================================================================
            # STEP 1: Check if data has changed and retrain model if needed
            # ================================================================
            logger.info("      - Checking if model retraining is needed...")
            
            try:
                retrain_needed, retrain_reason = await self._check_if_retrain_needed()
                
                if retrain_needed:
                    logger.info(f"      - Model retraining triggered: {retrain_reason}")
                    retraining_result = await self._retrain_prophet_model()
                    model_retrained = retraining_result.get("success", False)
                    
                    if model_retrained:
                        logger.info(f"      - Model retrained successfully: {retraining_result.get('training_rows', 0)} rows, MAPE: {retraining_result.get('mape', 'N/A')}")
                    else:
                        logger.warning(f"      - Model retraining failed: {retraining_result.get('error', 'Unknown error')}")
                else:
                    logger.info(f"      - No retraining needed: {retrain_reason}")
            except Exception as e:
                logger.warning(f"      - Retraining check failed: {e}")
                retrain_reason = f"Retraining check error: {e}"
            
            # ================================================================
            # STEP 2: Get event context for forecast explanations
            # ================================================================
            try:
                event_context = query_event_context.invoke({
                    "query": "upcoming events traffic demand",
                    "n_results": 10
                })
            except Exception as e:
                logger.warning(f"    Event context query failed: {e}")
                event_context = "No event context available"
            
            # ================================================================
            # STEP 3: Generate forecasts for each pricing model
            # ================================================================
            logger.info("      - Generating forecasts...")
            
            for pricing_model in ["CONTRACTED", "STANDARD", "CUSTOM"]:
                for periods in [30, 60, 90]:
                    try:
                        # Generate forecast
                        forecast_result = generate_prophet_forecast.invoke({
                            "pricing_model": pricing_model,
                            "periods": periods
                        })
                        
                        # Parse result if it's a string
                        if isinstance(forecast_result, str):
                            try:
                                forecast_result = json.loads(forecast_result)
                            except json.JSONDecodeError:
                                forecast_result = {"raw": forecast_result}
                        
                        key = f"{pricing_model}_{periods}d"
                        
                        # Generate explanation for this forecast
                        try:
                            explained = explain_forecast.invoke({
                                "forecast_data": forecast_result,
                                "event_context": event_context
                            })
                            
                            if isinstance(explained, dict):
                                # Add explanation to forecast result
                                forecast_result["explanation"] = explained.get("explanation", "")
                                forecast_result["context"] = explained.get("context", {})
                                explanations[key] = explained.get("explanation", "")
                            else:
                                forecast_result["explanation"] = str(explained)
                                explanations[key] = str(explained)
                        except Exception as e:
                            logger.warning(f"    Explanation generation for {key} failed: {e}")
                            forecast_result["explanation"] = f"Forecast generated but explanation unavailable: {e}"
                        
                        forecasts[key] = forecast_result
                        
                    except Exception as e:
                        logger.warning(f"    Forecast {pricing_model}/{periods}d failed: {e}")
                        forecasts[f"{pricing_model}_{periods}d"] = {"error": str(e)}
            
            # Generate summary explanation for all forecasts
            summary_explanation = self._generate_forecast_summary(forecasts)
            
            return {
                "success": True,
                "data": {
                    "model_retrained": model_retrained,
                    "retraining_info": retraining_result if model_retrained else {"reason": retrain_reason},
                    "forecasts": forecasts,
                    "explanations": explanations,
                    "summary_explanation": summary_explanation,
                    "event_context_used": event_context[:200] if isinstance(event_context, str) else "Context available",
                    "generated_at": datetime.utcnow().isoformat()
                }
            }
            
        except Exception as e:
            logger.error(f"    Forecasting phase error: {e}")
            return {"success": False, "error": str(e)}
    
    async def _check_if_retrain_needed(self) -> Tuple[bool, str]:
        """
        Check if Prophet ML model retraining is needed based on data changes.
        
        Returns:
            Tuple of (retrain_needed: bool, reason: str)
        """
        try:
            import pymongo
            from app.config import settings
            
            client = pymongo.MongoClient(settings.mongodb_url)
            db = client[settings.mongodb_db_name]
            
            try:
                # Collections that affect forecasting
                forecast_relevant_collections = ["historical_rides", "competitor_prices"]
                
                # Get the changes summary from the pipeline run
                # Check if any forecast-relevant collections have changed
                from app.agents.data_ingestion import change_tracker
                collections_changed = change_tracker.get_collections_changed()
                
                data_changed = any(
                    col in forecast_relevant_collections 
                    for col in collections_changed
                )
                
                if data_changed:
                    changed_cols = [c for c in collections_changed if c in forecast_relevant_collections]
                    return True, f"Data changed in: {', '.join(changed_cols)}"
                
                # Also check last training timestamp vs latest data
                metadata_collection = db["ml_training_metadata"]
                last_training = metadata_collection.find_one({"type": "last_training"})
                
                if not last_training:
                    return True, "No previous training record found"
                
                last_training_time = last_training.get("timestamp")
                
                # Check if there's newer data than last training
                historical_collection = db["historical_rides"]
                latest_doc = historical_collection.find_one(
                    {},
                    sort=[("Order_Date", -1), ("created_at", -1), ("_id", -1)]
                )
                
                if latest_doc:
                    latest_timestamp = None
                    if "Order_Date" in latest_doc:
                        latest_timestamp = latest_doc["Order_Date"]
                    elif "created_at" in latest_doc:
                        latest_timestamp = latest_doc["created_at"]
                    elif "_id" in latest_doc:
                        latest_timestamp = latest_doc["_id"].generation_time
                    
                    if latest_timestamp and last_training_time:
                        if isinstance(latest_timestamp, datetime) and isinstance(last_training_time, datetime):
                            if latest_timestamp > last_training_time:
                                return True, f"New data since last training ({latest_timestamp} > {last_training_time})"
                
                return False, "Model is up to date with current data"
                
            finally:
                client.close()
                
        except Exception as e:
            # If we can't check, err on the side of retraining
            return True, f"Could not verify model status: {e}"
    
    async def _retrain_prophet_model(self) -> Dict[str, Any]:
        """
        Retrain the Prophet ML model with COMBINED HWCO + competitor data.
        
        Using both datasets improves forecast accuracy:
        - More data points for better pattern recognition
        - Market-wide demand patterns (not just HWCO)
        - Competitive context helps predict HWCO-specific demand
        
        The model uses 'Rideshare_Company' as a regressor to differentiate
        between HWCO and competitor patterns while learning shared patterns
        (weekly cycles, time-of-day patterns, etc.).
        
        Returns:
            Dict with training results including data source breakdown
        """
        try:
            import pymongo
            import pandas as pd
            from app.config import settings
            from app.forecasting_ml import RideshareForecastModel
            
            logger.info("      - Loading HWCO + competitor data for retraining...")
            
            client = pymongo.MongoClient(settings.mongodb_url)
            db = client[settings.mongodb_db_name]
            
            try:
                # ============================================================
                # STEP 1: Load HWCO historical data
                # ============================================================
                historical_collection = db["historical_rides"]
                hwco_records = list(historical_collection.find({}))
                hwco_count = len(hwco_records)
                logger.info(f"      - HWCO records: {hwco_count}")
                
                # ============================================================
                # STEP 2: Load competitor (Lyft) data
                # ============================================================
                competitor_collection = db["competitor_prices"]
                competitor_records = list(competitor_collection.find({}))
                competitor_count = len(competitor_records)
                logger.info(f"      - Competitor records: {competitor_count}")
                
                # ============================================================
                # STEP 3: Standardize and combine datasets
                # ============================================================
                combined_records = []
                
                # Process HWCO records
                for record in hwco_records:
                    standardized = self._standardize_record_for_training(record, "HWCO")
                    if standardized:
                        combined_records.append(standardized)
                
                # Process competitor records
                for record in competitor_records:
                    standardized = self._standardize_record_for_training(record, "COMPETITOR")
                    if standardized:
                        combined_records.append(standardized)
                
                total_count = len(combined_records)
                logger.info(f"      - Combined training records: {total_count}")
                
                if total_count < 300:
                    return {
                        "success": False,
                        "error": f"Insufficient combined data: {total_count} rows (minimum 300 required)",
                        "hwco_count": hwco_count,
                        "competitor_count": competitor_count
                    }
                
                # Convert to DataFrame
                df = pd.DataFrame(combined_records)
                
                logger.info(f"      - Training model with {total_count} combined records (HWCO: {hwco_count}, Competitor: {competitor_count})...")
                
                # ============================================================
                # STEP 4: Train the model
                # ============================================================
                model = RideshareForecastModel()
                result = model.train(df)
                
                if result.get("success", False):
                    # Update training metadata with data source info
                    metadata_collection = db["ml_training_metadata"]
                    metadata_collection.update_one(
                        {"type": "last_training"},
                        {
                            "$set": {
                                "timestamp": datetime.utcnow(),
                                "training_rows": result.get("training_rows", 0),
                                "hwco_rows": hwco_count,
                                "competitor_rows": competitor_count,
                                "mape": result.get("mape", 0.0),
                                "triggered_by": "pipeline_forecasting_phase",
                                "data_sources": ["historical_rides", "competitor_prices"]
                            }
                        },
                        upsert=True
                    )
                    
                    logger.info(f"      - Model retrained successfully!")
                    logger.info(f"        Total rows: {result.get('training_rows', 0)}")
                    logger.info(f"        HWCO: {hwco_count}, Competitor: {competitor_count}")
                    
                    # Add data source breakdown to result
                    result["hwco_rows"] = hwco_count
                    result["competitor_rows"] = competitor_count
                    result["data_sources"] = ["historical_rides", "competitor_prices"]
                    
                return result
                
            finally:
                client.close()
                
        except Exception as e:
            logger.error(f"      - Model retraining failed: {e}")
            return {"success": False, "error": str(e)}
    
    def _standardize_record_for_training(self, record: Dict, source: str) -> Optional[Dict]:
        """
        Standardize a record from either HWCO or competitor data for Prophet training.
        
        Maps different field names to a common format and adds source identifier.
        
        Args:
            record: Raw record from MongoDB
            source: "HWCO" or "COMPETITOR"
            
        Returns:
            Standardized record dict, or None if record is invalid
        """
        try:
            standardized = {}
            
            # ============================================================
            # Map date field (Order_Date / completed_at / date)
            # ============================================================
            date_val = None
            for field in ["Order_Date", "completed_at", "date", "timestamp", "ds"]:
                if field in record and record[field]:
                    date_val = record[field]
                    break
            
            if not date_val:
                return None
            standardized["Order_Date"] = date_val
            
            # ============================================================
            # Map price/cost field (Historical_Cost_of_Ride / actual_price / price)
            # ============================================================
            price_val = None
            for field in ["Historical_Cost_of_Ride", "actual_price", "price", "cost", "y"]:
                if field in record and record[field] is not None:
                    try:
                        price_val = float(record[field])
                        break
                    except (ValueError, TypeError):
                        continue
            
            if price_val is None or price_val <= 0:
                return None
            standardized["Historical_Cost_of_Ride"] = price_val
            
            # ============================================================
            # Map pricing model (Pricing_Model / pricing_model / type)
            # ============================================================
            pricing_model = "STANDARD"  # Default
            for field in ["Pricing_Model", "pricing_model", "type", "service_type"]:
                if field in record and record[field]:
                    val = str(record[field]).upper()
                    if val in ["CONTRACTED", "STANDARD", "CUSTOM"]:
                        pricing_model = val
                        break
                    # Map competitor service types to our pricing models
                    elif "SHARE" in val or "POOL" in val:
                        pricing_model = "CONTRACTED"
                    elif "XL" in val or "PREMIUM" in val or "BLACK" in val:
                        pricing_model = "CUSTOM"
                    else:
                        pricing_model = "STANDARD"
                    break
            standardized["Pricing_Model"] = pricing_model
            
            # ============================================================
            # Map customer loyalty (Customer_Loyalty_Status)
            # ============================================================
            loyalty = "Regular"  # Default
            for field in ["Customer_Loyalty_Status", "loyalty_status", "loyalty_tier", "customer_tier"]:
                if field in record and record[field]:
                    val = str(record[field]).title()
                    if val in ["Gold", "Silver", "Regular"]:
                        loyalty = val
                        break
            standardized["Customer_Loyalty_Status"] = loyalty
            
            # ============================================================
            # Map location category (Location_Category)
            # ============================================================
            location = "Urban"  # Default
            for field in ["Location_Category", "location_category", "area_type", "zone"]:
                if field in record and record[field]:
                    val = str(record[field]).title()
                    if val in ["Urban", "Suburban", "Rural"]:
                        location = val
                        break
            standardized["Location_Category"] = location
            
            # ============================================================
            # Map vehicle type (Vehicle_Type)
            # ============================================================
            vehicle = "Economy"  # Default
            for field in ["Vehicle_Type", "vehicle_type", "car_type", "service_level"]:
                if field in record and record[field]:
                    val = str(record[field]).title()
                    if "Premium" in val or "Xl" in val or "Black" in val or "Lux" in val:
                        vehicle = "Premium"
                    else:
                        vehicle = "Economy"
                    break
            standardized["Vehicle_Type"] = vehicle
            
            # ============================================================
            # Map demand profile (Demand_Profile)
            # ============================================================
            demand = "MEDIUM"  # Default
            for field in ["Demand_Profile", "demand_profile", "surge_level"]:
                if field in record and record[field]:
                    val = str(record[field]).upper()
                    if val in ["HIGH", "MEDIUM", "LOW"]:
                        demand = val
                        break
            standardized["Demand_Profile"] = demand
            
            # ============================================================
            # Map time of ride (Time_of_Ride)
            # ============================================================
            time_of_ride = "Afternoon"  # Default
            for field in ["Time_of_Ride", "time_of_ride", "time_period"]:
                if field in record and record[field]:
                    val = str(record[field]).title()
                    if val in ["Morning", "Afternoon", "Evening", "Night"]:
                        time_of_ride = val
                        break
            standardized["Time_of_Ride"] = time_of_ride
            
            # ============================================================
            # Add source identifier (HWCO or COMPETITOR)
            # ============================================================
            standardized["Rideshare_Company"] = source
            
            return standardized
            
        except Exception as e:
            logger.debug(f"Failed to standardize record: {e}")
            return None
    
    def _generate_forecast_summary(self, forecasts: Dict) -> str:
        """Generate a summary explanation for all forecasts."""
        try:
            from openai import OpenAI
            from app.config import settings
            
            if not settings.OPENAI_API_KEY:
                return "Forecasts generated for all pricing models (30/60/90 days). See individual explanations for details."
            
            client = OpenAI(api_key=settings.OPENAI_API_KEY)
            
            # Extract key metrics
            summary_data = []
            for key, data in forecasts.items():
                if "error" not in data and data.get("forecast"):
                    avg_demand = sum(p.get("predicted_demand", 0) for p in data.get("forecast", [])) / len(data.get("forecast", [1]))
                    summary_data.append(f"{key}: avg {avg_demand:.1f} rides/day")
            
            prompt = f"""
            Provide a 2-sentence executive summary of these demand forecasts:
            {'; '.join(summary_data[:6])}
            
            Focus on trends, highest demand periods, and recommendations for resource planning.
            """
            
            response = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[{"role": "user", "content": prompt}],
                max_tokens=150
            )
            
            return response.choices[0].message.content.strip()
            
        except Exception as e:
            return "Forecasts generated successfully. Review individual model forecasts for detailed predictions."
    
    async def _run_analysis_phase(self) -> Dict[str, Any]:
        """
        Run the Analysis Agent for comprehensive data analysis WITH EXPLANATIONS.
        
        Includes:
        - Competitor analysis (HWCO vs competitors)
        - External data analysis (news, events, traffic)
        - Dynamic pricing rules regeneration
        
        Each analysis includes a natural language explanation.
        """
        logger.info("    → Running Analysis Agent...")
        
        try:
            # Import analysis tools
            from app.agents.analysis import (
                analyze_customer_segments,
                analyze_location_performance,
                analyze_time_patterns,
                get_top_revenue_rides,
                calculate_revenue_kpis
            )
            
            analysis_results = {}
            explanations = {}
            
            # 1. Competitor Analysis (HWCO vs historical competitor data)
            logger.info("      - Analyzing competitor data...")
            try:
                from app.agents.analysis import analyze_competitor_data_for_pipeline
                competitor_result = analyze_competitor_data_for_pipeline.invoke({})
                
                # Parse JSON result to extract explanation
                if isinstance(competitor_result, str):
                    try:
                        competitor_data = json.loads(competitor_result)
                        explanations["competitor"] = competitor_data.get("explanation", "")
                        analysis_results["competitor"] = competitor_data
                    except json.JSONDecodeError:
                        analysis_results["competitor"] = {"raw": competitor_result}
                else:
                    explanations["competitor"] = competitor_result.get("explanation", "")
                    analysis_results["competitor"] = competitor_result
            except Exception as e:
                logger.warning(f"      Competitor analysis failed: {e}")
                analysis_results["competitor"] = {"error": str(e)}
            
            # 2. External Data Analysis (news, events, traffic)
            logger.info("      - Analyzing external data...")
            try:
                from app.agents.analysis import analyze_external_data_for_pipeline
                external_result = analyze_external_data_for_pipeline.invoke({})
                
                # Parse JSON result to extract explanation
                if isinstance(external_result, str):
                    try:
                        external_data = json.loads(external_result)
                        explanations["external"] = external_data.get("explanation", "")
                        analysis_results["external"] = external_data
                    except json.JSONDecodeError:
                        analysis_results["external"] = {"raw": external_result}
                else:
                    explanations["external"] = external_result.get("explanation", "")
                    analysis_results["external"] = external_result
            except Exception as e:
                logger.warning(f"      External data analysis failed: {e}")
                analysis_results["external"] = {"error": str(e)}
            
            # 3. Dynamic Pricing Rules Generation
            logger.info("      - Generating pricing rules...")
            try:
                from app.agents.analysis import generate_pricing_rules_for_pipeline
                pricing_result = generate_pricing_rules_for_pipeline.invoke({})
                
                # Parse JSON result to extract explanation
                if isinstance(pricing_result, str):
                    try:
                        pricing_data = json.loads(pricing_result)
                        explanations["pricing_rules"] = pricing_data.get("explanation", "")
                        analysis_results["pricing_rules"] = pricing_data
                    except json.JSONDecodeError:
                        analysis_results["pricing_rules"] = {"raw": pricing_result}
                else:
                    explanations["pricing_rules"] = pricing_result.get("explanation", "")
                    analysis_results["pricing_rules"] = pricing_result
            except Exception as e:
                logger.warning(f"      Pricing rules generation failed: {e}")
                analysis_results["pricing_rules"] = {"error": str(e)}
            
            # 4. Run existing analysis tools for KPIs
            logger.info("      - Calculating KPIs...")
            try:
                kpi_result = calculate_revenue_kpis.invoke({"time_period": "30d"})
                analysis_results["kpis"] = json.loads(kpi_result) if isinstance(kpi_result, str) else kpi_result
            except Exception as e:
                logger.warning(f"      KPI calculation failed: {e}")
                analysis_results["kpis"] = {"error": str(e)}
            
            # Generate summary explanation for all analysis
            summary_explanation = self._generate_analysis_summary(analysis_results, explanations)
            
            return {
                "success": True,
                "data": {
                    "analysis": analysis_results,
                    "explanations": explanations,
                    "summary_explanation": summary_explanation,
                    "generated_at": datetime.utcnow().isoformat()
                }
            }
            
        except Exception as e:
            logger.error(f"    Analysis phase error: {e}")
            return {"success": False, "error": str(e)}
    
    def _generate_analysis_summary(self, results: Dict, explanations: Dict) -> str:
        """Generate a summary explanation consolidating all analysis insights."""
        try:
            # Combine individual explanations
            parts = []
            if explanations.get("competitor"):
                parts.append(f"Competitor: {explanations['competitor']}")
            if explanations.get("external"):
                parts.append(f"Market: {explanations['external']}")
            if explanations.get("pricing_rules"):
                parts.append(f"Pricing: {explanations['pricing_rules']}")
            
            if parts:
                return " | ".join(parts)
            return "Analysis completed. See individual sections for detailed insights."
            
        except Exception as e:
            return "Analysis completed successfully."
    
    async def _run_recommendation_phase(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Run the Recommendation Agent to generate strategic recommendations WITH EXPLANATIONS.
        
        Uses context from Forecasting and Analysis phases.
        The generate_strategic_recommendation tool returns:
        - recommendation: The strategic recommendation
        - reasoning: Why this recommendation (explanation)
        - expected_impact: Projected business impact
        """
        logger.info("    → Running Recommendation Agent...")
        
        try:
            from app.agents.recommendation import generate_strategic_recommendation, query_strategy_knowledge
            
            # Query strategy knowledge first for context
            try:
                strategy_context = query_strategy_knowledge.invoke({
                    "query": "revenue optimization pricing strategy competitive positioning",
                    "n_results": 10
                })
            except Exception as e:
                logger.warning(f"    Strategy knowledge query failed: {e}")
                strategy_context = "Strategic knowledge unavailable"
            
            # Extract explanations from analysis phase
            analysis_explanations = context.get("analysis", {}).get("explanations", {})
            forecast_summary = context.get("forecasting", {}).get("summary_explanation", "")
            
            # Prepare enriched context for recommendation agent
            inner_context = {
                "strategy_knowledge": strategy_context,
                "recent_events": json.dumps(context.get("analysis", {}).get("analysis", {}).get("external", {})),
                "competitor_data": json.dumps(context.get("analysis", {}).get("analysis", {}).get("competitor", {})),
                "forecast_data": context.get("forecasting", {}).get("forecasts", {}),
                "mongodb_ids": [],
                # Include explanations for better context
                "analysis_insights": analysis_explanations,
                "forecast_insights": forecast_summary
            }
            
            # Generate strategic recommendation (includes reasoning/explanation)
            # LangChain tools expect {"param_name": value} format
            result = generate_strategic_recommendation.invoke({"context": inner_context})
            
            if isinstance(result, str):
                try:
                    result = json.loads(result)
                except json.JSONDecodeError:
                    result = {"recommendation": result, "reasoning": "See recommendation text"}
            
            # Extract explanation components
            explanation = result.get("reasoning", result.get("recommendation", ""))
            
            return {
                "success": True,
                "data": {
                    "recommendations": result,
                    "explanation": explanation,
                    "expected_impact": result.get("expected_impact", {}),
                    "strategy_context_used": strategy_context[:200] if isinstance(strategy_context, str) else "Context available",
                    "generated_at": datetime.utcnow().isoformat()
                }
            }
            
        except Exception as e:
            logger.error(f"    Recommendation phase error: {e}")
            return {"success": False, "error": str(e)}
    
    async def _run_whatif_phase(self, recommendations: Dict[str, Any]) -> Dict[str, Any]:
        """
        Run What-If Impact Analysis on the recommendations WITH EXPLANATIONS.
        
        Calculates expected impact on KPIs and business objectives.
        Returns natural language explanation of impact.
        """
        logger.info("    → Running What-If Impact Analysis...")
        
        try:
            from app.agents.analysis import calculate_whatif_impact_for_pipeline
            
            # Calculate impact (includes explanation)
            result = calculate_whatif_impact_for_pipeline.invoke({
                "recommendations": json.dumps(recommendations)
            })
            
            if isinstance(result, str):
                try:
                    result = json.loads(result)
                except json.JSONDecodeError:
                    result = {"impact": result}
            
            # Extract explanation
            explanation = result.get("explanation", "")
            
            return {
                "success": True,
                "data": {
                    "impact_analysis": result,
                    "explanation": explanation,
                    "business_objectives_alignment": result.get("business_objectives_alignment", {}),
                    "generated_at": datetime.utcnow().isoformat()
                }
            }
            
        except Exception as e:
            logger.error(f"    What-If phase error: {e}")
            return {"success": False, "error": str(e)}
    
    async def _save_run_record(self, record: Dict[str, Any]) -> None:
        """Save pipeline run record to MongoDB."""
        try:
            import pymongo
            
            client = pymongo.MongoClient(settings.mongodb_url)
            db = client[settings.mongodb_db_name]
            collection = db["pipeline_results"]
            
            # Convert datetime objects for MongoDB
            record_copy = record.copy()
            if isinstance(record_copy.get("started_at"), datetime):
                record_copy["started_at"] = record_copy["started_at"]
            if isinstance(record_copy.get("completed_at"), datetime):
                record_copy["completed_at"] = record_copy["completed_at"]
            
            # Upsert by run_id
            collection.update_one(
                {"run_id": record["run_id"]},
                {"$set": record_copy},
                upsert=True
            )
            
            client.close()
            logger.debug(f"Pipeline record saved: {record['run_id']}")
            
        except Exception as e:
            logger.error(f"Failed to save pipeline record: {e}")


# Global pipeline instance
agent_pipeline = AgentPipeline()


async def run_agent_pipeline(
    trigger_source: str,
    changes_summary: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    Run the full agent pipeline.
    
    This is the main entry point for pipeline execution.
    Can be called from:
    - Hourly scheduler (background_tasks.py)
    - Manual API trigger (routers/pipeline.py)
    
    Args:
        trigger_source: "scheduled_hourly" or "manual_api"
        changes_summary: Summary of MongoDB changes
        
    Returns:
        Pipeline execution results
    """
    return await agent_pipeline.run(trigger_source, changes_summary)


def get_pipeline_status() -> Dict[str, Any]:
    """Get current pipeline status."""
    return {
        "is_running": agent_pipeline.is_running(),
        "current_run_id": agent_pipeline.current_run_id,
        "current_status": agent_pipeline.current_status
    }


async def get_pipeline_history(limit: int = 10) -> List[Dict[str, Any]]:
    """Get recent pipeline run history from MongoDB."""
    try:
        import pymongo
        
        client = pymongo.MongoClient(settings.mongodb_url)
        db = client[settings.mongodb_db_name]
        collection = db["pipeline_results"]
        
        # Get recent runs sorted by start time
        runs = list(collection.find({}).sort("started_at", -1).limit(limit))
        
        # Convert ObjectId to string
        for run in runs:
            run["_id"] = str(run["_id"])
        
        client.close()
        return runs
        
    except Exception as e:
        logger.error(f"Failed to get pipeline history: {e}")
        return []
