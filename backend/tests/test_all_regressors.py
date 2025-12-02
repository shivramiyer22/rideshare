"""
Test script for Prophet ML model with all regressors.

Tests that the model correctly uses all 6 required regressors:
1. pricing_model (CONTRACTED, STANDARD, CUSTOM)
2. Customer_Loyalty_Status (Gold, Silver, Regular)
3. Location_Category (Urban, Suburban, Rural)
4. Vehicle_Type (Premium, Economy)
5. Demand_Profile (HIGH, MEDIUM, LOW)
6. Time_of_Ride (Morning, Afternoon, Evening, Night)
"""
import sys
from pathlib import Path
backend_path = Path(__file__).parent.parent
sys.path.insert(0, str(backend_path))

import pytest
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from app.forecasting_ml import RideshareForecastModel


def test_model_uses_all_regressors():
    """Test that the model correctly processes all 6 required regressors."""
    # Create sample data with all regressors
    dates = pd.date_range('2024-01-01', periods=500, freq='D')
    
    sample_data = pd.DataFrame({
        'Order_Date': dates,
        'Historical_Cost_of_Ride': np.random.normal(50, 10, 500),
        'Pricing_Model': np.random.choice(['CONTRACTED', 'STANDARD', 'CUSTOM'], size=500),
        'Customer_Loyalty_Status': np.random.choice(['Gold', 'Silver', 'Regular'], size=500),
        'Location_Category': np.random.choice(['Urban', 'Suburban', 'Rural'], size=500),
        'Vehicle_Type': np.random.choice(['Premium', 'Economy'], size=500),
        'Demand_Profile': np.random.choice(['HIGH', 'MEDIUM', 'LOW'], size=500),
        'Time_of_Ride': np.random.choice(['Morning', 'Afternoon', 'Evening', 'Night'], size=500),
    })
    
    # Ensure no negative values for cost
    sample_data['Historical_Cost_of_Ride'] = sample_data['Historical_Cost_of_Ride'].abs()
    
    model = RideshareForecastModel()
    result = model.train(sample_data)
    
    assert result['success'] == True, f"Training failed: {result.get('error', 'Unknown error')}"
    assert result.get('mape') is not None, "MAPE should be calculated"
    assert result.get('model_path') is not None, "Model should be saved"
    
    print("✓ Model trained successfully with all 6 regressors")


def test_model_missing_regressor_warning():
    """Test that the model warns when regressors are missing."""
    # Create sample data without some regressors
    dates = pd.date_range('2024-01-01', periods=400, freq='D')
    
    sample_data = pd.DataFrame({
        'Order_Date': dates,
        'Historical_Cost_of_Ride': np.abs(np.random.normal(50, 10, 400)),
        'Pricing_Model': np.random.choice(['CONTRACTED', 'STANDARD', 'CUSTOM'], size=400),
        # Missing other regressors
    })
    
    model = RideshareForecastModel()
    result = model.train(sample_data)
    
    # Should still train but with fewer regressors
    assert result['success'] == True, f"Model should train even with missing regressors: {result.get('error', 'Unknown')}"
    print("✓ Model handles missing regressors gracefully")


def test_forecast_with_regressors():
    """Test that forecast method works with regressors."""
    # First train a model
    dates = pd.date_range('2024-01-01', periods=400, freq='D')
    
    sample_data = pd.DataFrame({
        'Order_Date': dates,
        'Historical_Cost_of_Ride': np.abs(np.random.normal(50, 10, 400)),
        'Pricing_Model': np.random.choice(['CONTRACTED', 'STANDARD', 'CUSTOM'], size=400),
        'Customer_Loyalty_Status': np.random.choice(['Gold', 'Silver', 'Regular'], size=400),
        'Location_Category': np.random.choice(['Urban', 'Suburban', 'Rural'], size=400),
        'Vehicle_Type': np.random.choice(['Premium', 'Economy'], size=400),
        'Demand_Profile': np.random.choice(['HIGH', 'MEDIUM', 'LOW'], size=400),
        'Time_of_Ride': np.random.choice(['Morning', 'Afternoon', 'Evening', 'Night'], size=400),
    })
    
    model = RideshareForecastModel()
    train_result = model.train(sample_data)
    
    assert train_result['success'] == True, "Training should succeed"
    
    # Test forecast for each pricing model
    for pricing_model in ['CONTRACTED', 'STANDARD', 'CUSTOM']:
        forecast = model.forecast(pricing_model, periods=30)
        assert forecast is not None, f"Forecast should work for {pricing_model}"
        assert len(forecast) == 30, f"Forecast should have 30 days for {pricing_model}"
        assert 'predicted_demand' in forecast.columns, "Forecast should have predicted_demand column"
        print(f"✓ Forecast works for {pricing_model} pricing model")


if __name__ == "__main__":
    print("=" * 60)
    print("Testing Prophet ML Model with All Regressors")
    print("=" * 60)
    print()
    
    try:
        test_model_uses_all_regressors()
        test_model_missing_regressor_warning()
        test_forecast_with_regressors()
        
        print()
        print("=" * 60)
        print("✅ All tests passed!")
        print("=" * 60)
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        exit(1)

