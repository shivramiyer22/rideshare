"""
Test script for Prophet ML Forecasting.

Tests:
1. Model initialization
2. Data validation
3. Training with all pricing types (CONTRACTED, STANDARD, CUSTOM)
4. Model saving and loading
5. Forecasting for each pricing type (30/60/90 days)
6. Confidence intervals in forecasts

Run with: python -m pytest backend/tests/test_prophet_ml.py -v
Or: python backend/tests/test_prophet_ml.py
"""

import sys
import os
import tempfile
import shutil
from pathlib import Path
from datetime import datetime, timedelta

# Add backend to path
backend_path = Path(__file__).parent.parent
sys.path.insert(0, str(backend_path))

import pytest
import pandas as pd
import numpy as np

from app.forecasting_ml import RideshareForecastModel


class TestProphetML:
    """Test suite for Prophet ML Forecasting."""
    
    def __init__(self):
        """Initialize test suite."""
        self.temp_dir = None
    
    def create_sample_data(self, num_rows=1000):
        """Create sample historical data with all pricing types."""
        np.random.seed(42)  # For reproducible tests
        
        # Create dates
        start_date = datetime(2024, 1, 1)
        dates = [start_date + timedelta(days=i) for i in range(num_rows)]
        
        # Create pricing models distribution
        pricing_models = np.random.choice(
            ['CONTRACTED', 'STANDARD', 'CUSTOM'],
            size=num_rows,
            p=[0.2, 0.6, 0.2]  # 20% CONTRACTED, 60% STANDARD, 20% CUSTOM
        )
        
        # Create prices with different means per pricing type
        prices = []
        for pm in pricing_models:
            if pm == 'CONTRACTED':
                price = np.random.normal(45, 5)  # Fixed prices around $45
            elif pm == 'STANDARD':
                price = np.random.normal(50, 10)  # Standard prices around $50
            else:  # CUSTOM
                price = np.random.normal(55, 8)  # Custom prices around $55
            prices.append(max(10, price))  # Ensure positive prices
        
        df = pd.DataFrame({
            'completed_at': dates,
            'actual_price': prices,
            'pricing_model': pricing_models
        })
        
        return df
    
    def test_model_initialization(self):
        """Test model initialization."""
        print("\n" + "="*60)
        print("Test 1: Model Initialization")
        print("="*60)
        
        try:
            model = RideshareForecastModel(models_dir=self.temp_dir)
            
            # Verify models directory was created
            assert Path(self.temp_dir).exists(), "Models directory not created"
            print(f"  ✓ Models directory created: {self.temp_dir}")
            
            # Verify model exists
            assert model is not None, "Model not initialized"
            print(f"  ✓ Model initialized successfully")
            
            print(f"\n✓ Model initialization test passed")
            return True
            
        except Exception as e:
            print(f"\n✗ Model initialization failed: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def test_data_validation(self):
        """Test data validation."""
        print("\n" + "="*60)
        print("Test 2: Data Validation")
        print("="*60)
        
        try:
            model = RideshareForecastModel(models_dir=self.temp_dir)
            
            # Test 1: Empty DataFrame
            empty_df = pd.DataFrame()
            is_valid, error = model._validate_dataframe(empty_df)
            assert not is_valid, "Should reject empty DataFrame"
            print(f"  ✓ Empty DataFrame rejected: {error}")
            
            # Test 2: Missing required columns
            missing_cols_df = pd.DataFrame({'wrong_col': [1, 2, 3]})
            is_valid, error = model._validate_dataframe(missing_cols_df)
            assert not is_valid, "Should reject DataFrame with missing columns"
            print(f"  ✓ Missing columns rejected: {error}")
            
            # Test 3: Valid DataFrame
            valid_df = pd.DataFrame({
                'ds': pd.date_range('2024-01-01', periods=1000, freq='D'),
                'y': np.random.normal(50, 10, 1000)
            })
            is_valid, error = model._validate_dataframe(valid_df)
            assert is_valid, f"Should accept valid DataFrame: {error}"
            print(f"  ✓ Valid DataFrame accepted")
            
            # Test 4: Insufficient data (< 1000 rows)
            small_df = pd.DataFrame({
                'ds': pd.date_range('2024-01-01', periods=500, freq='D'),
                'y': np.random.normal(50, 10, 500)
            })
            is_valid, error = model._validate_dataframe(small_df)
            assert not is_valid, "Should reject DataFrame with < 1000 rows"
            print(f"  ✓ Insufficient data rejected: {error}")
            
            print(f"\n✓ Data validation test passed")
            return True
            
        except Exception as e:
            print(f"\n✗ Data validation test failed: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def test_training_all_pricing_types(self):
        """Test training with all pricing types in one model."""
        print("\n" + "="*60)
        print("Test 3: Training Model (All Pricing Types)")
        print("="*60)
        
        try:
            model = RideshareForecastModel(models_dir=self.temp_dir)
            
            # Create sample data with all pricing types
            sample_data = self.create_sample_data(1000)
            
            print(f"  → Training data: {len(sample_data)} rows")
            print(f"    - CONTRACTED: {len(sample_data[sample_data['pricing_model'] == 'CONTRACTED'])} orders")
            print(f"    - STANDARD: {len(sample_data[sample_data['pricing_model'] == 'STANDARD'])} orders")
            print(f"    - CUSTOM: {len(sample_data[sample_data['pricing_model'] == 'CUSTOM'])} orders")
            
            # Train model (single model for all pricing types)
            result = model.train(sample_data)
            
            assert result["success"], f"Training failed: {result.get('error', 'Unknown error')}"
            print(f"  ✓ Training successful")
            print(f"    - MAPE: {result['mape']:.2f}%")
            print(f"    - Model path: {result['model_path']}")
            print(f"    - Training rows: {result['training_rows']}")
            
            # Verify model file exists
            model_path = Path(result['model_path'])
            assert model_path.exists(), "Model file not created"
            print(f"  ✓ Model file exists: {model_path}")
            
            # Verify model can be loaded
            assert model._model_exists(), "Model existence check failed"
            print(f"  ✓ Model existence verified")
            
            print(f"\n✓ Training test passed")
            return True
            
        except Exception as e:
            print(f"\n✗ Training test failed: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def test_forecasting_all_pricing_types(self):
        """Test forecasting for each pricing type."""
        print("\n" + "="*60)
        print("Test 4: Forecasting (All Pricing Types)")
        print("="*60)
        
        try:
            model = RideshareForecastModel(models_dir=self.temp_dir)
            
            # First, train the model
            sample_data = self.create_sample_data(1000)
            train_result = model.train(sample_data)
            
            if not train_result["success"]:
                print(f"  ✗ Training failed, cannot test forecasting")
                return False
            
            # Test forecasting for each pricing type
            pricing_types = ['CONTRACTED', 'STANDARD', 'CUSTOM']
            periods_options = [30, 60, 90]
            
            all_passed = True
            for pricing_type in pricing_types:
                for periods in periods_options:
                    try:
                        forecast = model.forecast(pricing_type, periods)
                        
                        assert forecast is not None, f"Forecast returned None for {pricing_type}, {periods}d"
                        assert len(forecast) == periods, f"Forecast length mismatch for {pricing_type}, {periods}d"
                        
                        # Verify required columns
                        required_cols = ['date', 'predicted_demand', 'confidence_lower', 'confidence_upper', 'trend']
                        for col in required_cols:
                            assert col in forecast.columns, f"Missing column {col} in forecast"
                        
                        # Verify confidence intervals
                        assert all(forecast['confidence_lower'] <= forecast['predicted_demand']), \
                            f"confidence_lower > predicted_demand for {pricing_type}"
                        assert all(forecast['predicted_demand'] <= forecast['confidence_upper']), \
                            f"predicted_demand > confidence_upper for {pricing_type}"
                        
                        print(f"  ✓ {pricing_type} {periods}d forecast: "
                              f"avg={forecast['predicted_demand'].mean():.2f}, "
                              f"range=[{forecast['confidence_lower'].min():.2f}, {forecast['confidence_upper'].max():.2f}]")
                        
                    except Exception as e:
                        print(f"  ✗ Forecast failed for {pricing_type}, {periods}d: {e}")
                        all_passed = False
            
            if all_passed:
                print(f"\n✓ Forecasting test passed")
            else:
                print(f"\n✗ Some forecasting tests failed")
            
            return all_passed
            
        except Exception as e:
            print(f"\n✗ Forecasting test failed: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def test_insufficient_data_handling(self):
        """Test handling of insufficient data."""
        print("\n" + "="*60)
        print("Test 5: Insufficient Data Handling")
        print("="*60)
        
        try:
            model = RideshareForecastModel(models_dir=self.temp_dir)
            
            # Create data with less than 1000 rows
            small_data = self.create_sample_data(500)
            
            result = model.train(small_data)
            
            assert not result["success"], "Should reject data with < 1000 rows"
            assert "error" in result, "Error message not provided"
            assert "1000" in result["error"].lower(), "Error should mention 1000 row requirement"
            
            print(f"  ✓ Insufficient data correctly rejected: {result['error']}")
            print(f"\n✓ Insufficient data handling test passed")
            return True
            
        except Exception as e:
            print(f"\n✗ Insufficient data handling test failed: {e}")
            return False


def run_all_tests():
    """Run all tests and report results."""
    print("\n" + "="*60)
    print("PROPHET ML FORECASTING - TEST SUITE")
    print("="*60)
    
    # Create test instance
    test_suite = TestProphetML()
    
    # Manually setup test environment
    temp_dir = tempfile.mkdtemp()
    test_suite.temp_dir = temp_dir
    
    try:
        results = {
            "model_initialization": test_suite.test_model_initialization(),
            "data_validation": test_suite.test_data_validation(),
            "training": test_suite.test_training_all_pricing_types(),
            "forecasting": test_suite.test_forecasting_all_pricing_types(),
            "insufficient_data": test_suite.test_insufficient_data_handling()
        }
    finally:
        # Cleanup
        shutil.rmtree(temp_dir, ignore_errors=True)
    
    print("\n" + "="*60)
    print("TEST RESULTS SUMMARY")
    print("="*60)
    
    passed = sum(1 for v in results.values() if v)
    total = len(results)
    
    for test_name, result in results.items():
        status = "✓ PASSED" if result else "✗ FAILED"
        print(f"  {test_name}: {status}")
    
    print(f"\nTotal: {passed}/{total} tests passed")
    
    if passed == total:
        print("✓ ALL TESTS PASSED!")
        return True
    else:
        print("✗ SOME TESTS FAILED")
        return False


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)

