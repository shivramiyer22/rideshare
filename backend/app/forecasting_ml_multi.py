"""
Prophet ML Multi-Metric Forecasting with 24 Regressors

This module provides Prophet ML forecasting for 3 key metrics:
1. Demand (number of rides per day)
2. Duration (average ride duration in minutes per day)
3. Unit Price (average $/minute per day)

Each metric gets its own Prophet model trained with 24 regressors:
- 20 Categorical Regressors (one-hot encoded)
- 4 Numeric Regressors

The 24 Regressors:
- pricing_* (3): CONTRACTED, STANDARD, CUSTOM
- time_* (4): Morning, Afternoon, Evening, Night
- demand_* (3): HIGH, MEDIUM, LOW  
- location_* (3): Urban, Suburban, Rural
- loyalty_* (3): Gold, Silver, Regular
- vehicle_* (2): Premium, Economy
- company_* (2): HWCO, COMPETITOR
- num_riders (numeric): Number of riders per ride
- num_drivers (numeric): Available drivers
- ride_duration (numeric): Expected duration in minutes
- unit_price (numeric): Price per minute
"""

from prophet import Prophet
import pandas as pd
import pickle
from pathlib import Path
from typing import Dict, Any, Optional, Tuple
import logging

logger = logging.getLogger(__name__)


class MultiMetricForecastModel:
    """
    Simple multi-metric Prophet ML forecasting.
    
    Trains 3 separate Prophet models:
    - demand_model.pkl: Forecasts ride counts per day
    - duration_model.pkl: Forecasts average duration per day
    - unit_price_model.pkl: Forecasts average $/min per day
    """
    
    def __init__(self, models_dir: str = "./models"):
        """Initialize the multi-metric forecasting system."""
        self.models_dir = Path(models_dir)
        self.models_dir.mkdir(parents=True, exist_ok=True)
        
        self.model_files = {
            'demand': 'demand_model.pkl',
            'duration': 'duration_model.pkl',
            'unit_price': 'unit_price_model.pkl'
        }
        
        logger.info(f"Multi-metric Prophet ML initialized at {self.models_dir}")
    
    def _prepare_regressors(
        self,
        historical_data: pd.DataFrame,
        prophet_data: pd.DataFrame
    ) -> Tuple[pd.DataFrame, list]:
        """
        Prepare all 24 regressors for Prophet ML.
        
        Returns:
            Tuple of (prophet_data with regressors added, list of regressor column names)
        """
        regressor_cols = []
        
        # 1. Pricing_Model regressors (CONTRACTED, STANDARD, CUSTOM)
        pricing_col = None
        if 'Pricing_Model' in historical_data.columns:
            pricing_col = 'Pricing_Model'
        elif 'pricing_model' in historical_data.columns:
            pricing_col = 'pricing_model'
        
        if pricing_col:
            pricing_dummies = pd.get_dummies(historical_data[pricing_col], prefix='pricing')
            for col in pricing_dummies.columns:
                prophet_data[col] = pricing_dummies[col].values
                regressor_cols.append(col)
            logger.info(f"  → Added {len(pricing_dummies.columns)} Pricing_Model regressors")
        
        # 2. Time_of_Ride regressors (Morning, Afternoon, Evening, Night)
        if 'Time_of_Ride' in historical_data.columns:
            time_dummies = pd.get_dummies(historical_data['Time_of_Ride'], prefix='time')
            for col in time_dummies.columns:
                prophet_data[col] = time_dummies[col].values
                regressor_cols.append(col)
            logger.info(f"  → Added {len(time_dummies.columns)} Time_of_Ride regressors")
        
        # 3. Demand_Profile regressors (HIGH, MEDIUM, LOW)
        if 'Demand_Profile' in historical_data.columns:
            demand_dummies = pd.get_dummies(historical_data['Demand_Profile'], prefix='demand')
            for col in demand_dummies.columns:
                prophet_data[col] = demand_dummies[col].values
                regressor_cols.append(col)
            logger.info(f"  → Added {len(demand_dummies.columns)} Demand_Profile regressors")
        
        # 4. Location_Category regressors (Urban, Suburban, Rural)
        if 'Location_Category' in historical_data.columns:
            location_dummies = pd.get_dummies(historical_data['Location_Category'], prefix='location')
            for col in location_dummies.columns:
                prophet_data[col] = location_dummies[col].values
                regressor_cols.append(col)
            logger.info(f"  → Added {len(location_dummies.columns)} Location_Category regressors")
        
        # 5. Customer_Loyalty_Status regressors (Gold, Silver, Regular)
        loyalty_col = None
        if 'Customer_Loyalty_Status' in historical_data.columns:
            loyalty_col = 'Customer_Loyalty_Status'
        elif 'loyalty_status' in historical_data.columns:
            loyalty_col = 'loyalty_status'
        elif 'loyalty_tier' in historical_data.columns:
            loyalty_col = 'loyalty_tier'
        
        if loyalty_col:
            loyalty_dummies = pd.get_dummies(historical_data[loyalty_col], prefix='loyalty')
            for col in loyalty_dummies.columns:
                prophet_data[col] = loyalty_dummies[col].values
                regressor_cols.append(col)
            logger.info(f"  → Added {len(loyalty_dummies.columns)} Loyalty regressors")
        
        # 6. Vehicle_Type regressors (Premium, Economy)
        vehicle_col = None
        if 'Vehicle_Type' in historical_data.columns:
            vehicle_col = 'Vehicle_Type'
        elif 'vehicle_type' in historical_data.columns:
            vehicle_col = 'vehicle_type'
        
        if vehicle_col:
            vehicle_dummies = pd.get_dummies(historical_data[vehicle_col], prefix='vehicle')
            for col in vehicle_dummies.columns:
                prophet_data[col] = vehicle_dummies[col].values
                regressor_cols.append(col)
            logger.info(f"  → Added {len(vehicle_dummies.columns)} Vehicle_Type regressors")
        
        # 7. Rideshare_Company regressors (HWCO, COMPETITOR)
        if 'Rideshare_Company' in historical_data.columns:
            company_dummies = pd.get_dummies(historical_data['Rideshare_Company'], prefix='company')
            for col in company_dummies.columns:
                prophet_data[col] = company_dummies[col].values
                regressor_cols.append(col)
            logger.info(f"  → Added {len(company_dummies.columns)} Company regressors")
        
        # 8-11. Numeric regressors
        # num_riders
        if 'Number_Of_Riders' in historical_data.columns:
            prophet_data['num_riders'] = pd.to_numeric(historical_data['Number_Of_Riders'], errors='coerce')
            regressor_cols.append('num_riders')
            logger.info("  → Added num_riders regressor")
        
        # num_drivers
        if 'Number_of_Drivers' in historical_data.columns:
            prophet_data['num_drivers'] = pd.to_numeric(historical_data['Number_of_Drivers'], errors='coerce')
            regressor_cols.append('num_drivers')
            logger.info("  → Added num_drivers regressor")
        
        # ride_duration
        if 'Expected_Ride_Duration' in historical_data.columns:
            prophet_data['ride_duration'] = pd.to_numeric(historical_data['Expected_Ride_Duration'], errors='coerce')
            regressor_cols.append('ride_duration')
            logger.info("  → Added ride_duration regressor")
        
        # unit_price
        if 'Historical_Unit_Price' in historical_data.columns:
            prophet_data['unit_price'] = pd.to_numeric(historical_data['Historical_Unit_Price'], errors='coerce')
            regressor_cols.append('unit_price')
            logger.info("  → Added unit_price regressor")
        elif 'Historical_Cost_of_Ride' in historical_data.columns and 'Expected_Ride_Duration' in historical_data.columns:
            cost = pd.to_numeric(historical_data['Historical_Cost_of_Ride'], errors='coerce')
            duration = pd.to_numeric(historical_data['Expected_Ride_Duration'], errors='coerce')
            prophet_data['unit_price'] = (cost / duration).replace([float('inf'), -float('inf')], None)
            regressor_cols.append('unit_price')
            logger.info("  → Added unit_price regressor (calculated)")
        
        logger.info(f"  → Total regressors: {len(regressor_cols)}")
        
        return prophet_data, regressor_cols
    
    def _prepare_metric_data(
        self,
        historical_data: pd.DataFrame,
        metric: str
    ) -> Optional[Tuple[pd.DataFrame, list]]:
        """
        Prepare data for a specific metric in Prophet format (ds, y) with 24 regressors.
        
        Args:
            historical_data: Raw historical rides data
            metric: 'demand', 'duration', or 'unit_price'
            
        Returns:
            Tuple of (DataFrame with columns ['ds', 'y', ...regressors], list of regressor names)
            Returns None if insufficient data
        """
        try:
            # Extract date column
            if 'Order_Date' in historical_data.columns:
                ds = pd.to_datetime(historical_data['Order_Date'])
            elif 'completed_at' in historical_data.columns:
                ds = pd.to_datetime(historical_data['completed_at'])
            else:
                logger.error("No date column found")
                return None
            
            # Start with ds column
            prophet_data = pd.DataFrame({'ds': ds})
            
            # Prepare data based on metric type (y column)
            if metric == 'demand':
                # For demand: count rides per day (each row = 1 ride)
                prophet_data['y'] = 1.0
                
            elif metric == 'duration':
                # For duration: use Expected_Ride_Duration
                if 'Expected_Ride_Duration' not in historical_data.columns:
                    logger.error("Expected_Ride_Duration column not found")
                    return None
                
                duration = pd.to_numeric(historical_data['Expected_Ride_Duration'], errors='coerce')
                prophet_data['y'] = duration
                
            elif metric == 'unit_price':
                # For unit_price: use Historical_Unit_Price or calculate
                if 'Historical_Unit_Price' in historical_data.columns:
                    unit_price = pd.to_numeric(historical_data['Historical_Unit_Price'], errors='coerce')
                elif 'Historical_Cost_of_Ride' in historical_data.columns and 'Expected_Ride_Duration' in historical_data.columns:
                    cost = pd.to_numeric(historical_data['Historical_Cost_of_Ride'], errors='coerce')
                    duration = pd.to_numeric(historical_data['Expected_Ride_Duration'], errors='coerce')
                    unit_price = (cost / duration).replace([float('inf'), -float('inf')], None)
                else:
                    logger.error("Cannot calculate unit_price - missing required columns")
                    return None
                
                prophet_data['y'] = unit_price
            
            else:
                logger.error(f"Unknown metric: {metric}")
                return None
            
            # Add all 24 regressors to individual ride data
            prophet_data, regressor_cols = self._prepare_regressors(historical_data, prophet_data)
            
            # Remove rows with NaN in ds or y
            prophet_data = prophet_data.dropna(subset=['ds', 'y'])
            if metric == 'unit_price':
                prophet_data = prophet_data[prophet_data['y'] > 0]  # Remove invalid prices
            
            # Aggregate by date
            agg_dict = {}
            
            if metric == 'demand':
                # Sum rides per day
                agg_dict['y'] = 'sum'
            else:
                # Average duration or unit_price per day
                agg_dict['y'] = 'mean'
            
            # Aggregate regressors: mean for one-hot (gives proportion of rides with that feature)
            for col in regressor_cols:
                if col in prophet_data.columns:
                    agg_dict[col] = 'mean'
            
            prophet_data = prophet_data.groupby('ds').agg(agg_dict).reset_index()
            
            # Fill NaN in regressors with 0 (missing features)
            for col in regressor_cols:
                if col in prophet_data.columns:
                    prophet_data[col] = prophet_data[col].fillna(0)
            
            # Sort by date
            prophet_data = prophet_data.sort_values('ds').reset_index(drop=True)
            
            logger.info(f"  {metric}: {len(prophet_data)} days, {len(regressor_cols)} regressors, avg y={prophet_data['y'].mean():.2f}")
            
            if len(prophet_data) < 30:
                logger.warning(f"  {metric}: Only {len(prophet_data)} days - need at least 30")
                return None
            
            return prophet_data, regressor_cols
            
        except Exception as e:
            logger.error(f"Error preparing {metric} data: {e}")
            return None
    
    def _train_single_metric(
        self,
        historical_data: pd.DataFrame,
        metric: str
    ) -> Dict[str, Any]:
        """
        Train a single Prophet model for one metric with 24 regressors.
        
        Args:
            historical_data: Raw historical data
            metric: 'demand', 'duration', or 'unit_price'
            
        Returns:
            Dictionary with success, model_path, training_rows, num_regressors
        """
        try:
            logger.info(f"\nTraining {metric.upper()} model with 24 regressors...")
            
            # Prepare data with regressors
            result = self._prepare_metric_data(historical_data, metric)
            
            if result is None:
                return {
                    "success": False,
                    "error": f"Insufficient data for {metric}: need 30+ days"
                }
            
            prophet_data, regressor_cols = result
            
            if len(prophet_data) < 30:
                return {
                    "success": False,
                    "error": f"Insufficient data for {metric}: need 30+ days"
                }
            
            # Configure Prophet model
            model = Prophet(
                yearly_seasonality=False,
                weekly_seasonality=True,
                daily_seasonality=False,
                seasonality_mode='multiplicative',
                interval_width=0.80
            )
            
            # Add all regressors to the model
            logger.info(f"  Adding {len(regressor_cols)} regressors to {metric} model...")
            for regressor in regressor_cols:
                if regressor in prophet_data.columns:
                    model.add_regressor(regressor)
            
            # Train the model
            logger.info(f"  Training on {len(prophet_data)} days of data...")
            model.fit(prophet_data)
            
            # Save model
            model_path = self.models_dir / self.model_files[metric]
            with open(model_path, 'wb') as f:
                pickle.dump(model, f)
            
            logger.info(f"  ✓ {metric.upper()} model trained with {len(regressor_cols)} regressors and saved to {model_path.name}")
            
            return {
                "success": True,
                "model_path": str(model_path),
                "training_rows": len(prophet_data),
                "num_regressors": len(regressor_cols)
            }
            
        except Exception as e:
            logger.error(f"Error training {metric} model: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def train_all(self, historical_data: pd.DataFrame) -> Dict[str, Any]:
        """
        Train all 3 Prophet models.
        
        Args:
            historical_data: DataFrame with historical rides data
            
        Returns:
            Dictionary with overall success status and individual model results
        """
        logger.info("=" * 80)
        logger.info("TRAINING ALL 3 PROPHET ML MODELS")
        logger.info("=" * 80)
        logger.info(f"Input data: {len(historical_data)} individual rides")
        
        if len(historical_data) < 300:
            return {
                "success": False,
                "error": f"Insufficient data: {len(historical_data)} rides. Need 300+ rides."
            }
        
        results = {}
        
        # Train each metric
        for metric in ['demand', 'duration', 'unit_price']:
            result = self._train_single_metric(historical_data, metric)
            results[metric] = result
        
        # Check if all succeeded
        all_success = all(r.get('success', False) for r in results.values())
        
        if all_success:
            total_training_rows = sum(r.get('training_rows', 0) for r in results.values())
            logger.info("\n" + "=" * 80)
            logger.info("✓ ALL 3 MODELS TRAINED SUCCESSFULLY")
            logger.info("=" * 80)
            
            return {
                "success": True,
                "models_trained": list(results.keys()),
                "training_rows": results,
                "message": f"Successfully trained 3 Prophet ML models"
            }
        else:
            failed_models = [m for m, r in results.items() if not r.get('success', False)]
            logger.error(f"\n✗ Training failed for: {failed_models}")
            
            return {
                "success": False,
                "error": f"Training failed for: {', '.join(failed_models)}",
                "results": results
            }
    
    def forecast_all(self, periods: int = 30, historical_data: Optional[pd.DataFrame] = None) -> Optional[Dict[str, pd.DataFrame]]:
        """
        Generate forecasts for all 3 metrics with regressors.
        
        Args:
            periods: Number of days to forecast (30, 60, or 90)
            historical_data: Historical data to extract regressor mean values from.
                           If None, uses training data means for regressors.
            
        Returns:
            Dictionary with 'demand', 'duration', 'unit_price' DataFrames
            Each DataFrame has columns: ds, yhat, yhat_lower, yhat_upper
        """
        try:
            forecasts = {}
            
            # If historical data provided, calculate regressor means for future prediction
            regressor_means = {}
            if historical_data is not None and len(historical_data) > 0:
                try:
                    # Prepare regressors from historical data (just to get mean values)
                    temp_ds = pd.to_datetime(historical_data.iloc[:min(100, len(historical_data))].get('Order_Date', historical_data.get('completed_at')))
                    temp_data = pd.DataFrame({'ds': temp_ds})
                    temp_data, regressor_cols = self._prepare_regressors(
                        historical_data.iloc[:min(100, len(historical_data))], 
                        temp_data
                    )
                    
                    # Calculate mean values for each regressor
                    for col in regressor_cols:
                        if col in temp_data.columns:
                            regressor_means[col] = float(temp_data[col].mean())
                    
                    logger.info(f"Calculated means for {len(regressor_means)} regressors from historical data")
                except Exception as e:
                    logger.warning(f"Could not calculate regressor means: {e}")
                    regressor_means = {}
            
            for metric in ['demand', 'duration', 'unit_price']:
                model_path = self.models_dir / self.model_files[metric]
                
                if not model_path.exists():
                    logger.error(f"{metric} model not found at {model_path}")
                    return None
                
                # Load model
                with open(model_path, 'rb') as f:
                    model = pickle.load(f)
                
                # Generate future dataframe
                future = model.make_future_dataframe(periods=periods)
                
                # CRITICAL FIX: Use training data means for regressors, not zeros!
                # When regressors are 0, Prophet extrapolates to negative/unrealistic values
                for regressor in model.extra_regressors.keys():
                    if regressor in regressor_means:
                        # Use historical data mean if available
                        future[regressor] = regressor_means[regressor]
                    elif hasattr(model, 'history') and regressor in model.history.columns:
                        # Fallback: use training data mean for this regressor
                        future[regressor] = float(model.history[regressor].mean())
                        logger.info(f"  {metric}/{regressor}: using training mean {future[regressor].iloc[0]:.3f}")
                    else:
                        # Last resort: use 0 (may cause negative predictions)
                        future[regressor] = 0
                        logger.warning(f"  {metric}/{regressor}: no mean available, using 0")
                
                # Generate forecast
                forecast = model.predict(future)
                
                # Return only future predictions (last 'periods' rows)
                forecast = forecast.tail(periods)[['ds', 'yhat', 'yhat_lower', 'yhat_upper']]
                
                # IMPORTANT: Ensure non-negative predictions for demand and unit_price
                if metric in ['demand', 'unit_price']:
                    forecast['yhat'] = forecast['yhat'].clip(lower=0)
                    forecast['yhat_lower'] = forecast['yhat_lower'].clip(lower=0)
                    forecast['yhat_upper'] = forecast['yhat_upper'].clip(lower=0)
                elif metric == 'duration':
                    forecast['yhat'] = forecast['yhat'].clip(lower=1)  # Min 1 minute
                    forecast['yhat_lower'] = forecast['yhat_lower'].clip(lower=1)
                    forecast['yhat_upper'] = forecast['yhat_upper'].clip(lower=1)
                
                forecasts[metric] = forecast
                
                logger.info(f"  {metric}: {len(forecast)} days, yhat range [{forecast['yhat'].min():.2f}, {forecast['yhat'].max():.2f}]")
            
            return forecasts
            
        except Exception as e:
            logger.error(f"Error generating forecasts: {e}")
            return None

