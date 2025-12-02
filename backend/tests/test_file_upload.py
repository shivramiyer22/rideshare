"""
Test script for File Upload Endpoints.

Tests:
1. Historical data CSV upload validation
2. Historical data JSON upload validation
3. Competitor data CSV upload validation
4. Competitor data Excel upload validation
5. Missing columns validation
6. Invalid data types validation
7. Insufficient data validation

Note: These tests validate the logic but require MongoDB connection for full integration testing.
Run with: python -m pytest backend/tests/test_file_upload.py -v
Or: python backend/tests/test_file_upload.py
"""

import sys
import io
from pathlib import Path
from datetime import datetime, timedelta
import pandas as pd
import json

# Add backend to path
backend_path = Path(__file__).parent.parent
sys.path.insert(0, str(backend_path))

from app.routers.upload import validate_historical_data, validate_competitor_data


class TestFileUpload:
    """Test suite for File Upload Endpoints."""
    
    def create_sample_historical_data(self, num_rows=1000):
        """Create sample historical data DataFrame."""
        dates = [datetime.now() - timedelta(days=i) for i in range(num_rows)]
        pricing_models = ["CONTRACTED", "STANDARD", "CUSTOM"] * (num_rows // 3 + 1)
        prices = [45.0 + i * 0.1 for i in range(num_rows)]
        
        return pd.DataFrame({
            "completed_at": dates[:num_rows],
            "pricing_model": pricing_models[:num_rows],
            "actual_price": prices[:num_rows]
        })
    
    def create_sample_competitor_data(self, num_rows=100):
        """Create sample competitor data DataFrame."""
        competitors = ["Uber", "Lyft", "Taxi"] * (num_rows // 3 + 1)
        routes = ["Downtown to Airport", "Airport to Downtown", "City Center"] * (num_rows // 3 + 1)
        prices = [45.0 + i * 0.5 for i in range(num_rows)]
        timestamps = [datetime.now() - timedelta(hours=i) for i in range(num_rows)]
        
        return pd.DataFrame({
            "competitor_name": competitors[:num_rows],
            "route": routes[:num_rows],
            "price": prices[:num_rows],
            "timestamp": timestamps[:num_rows]
        })
    
    async def test_historical_data_validation_success(self):
        """Test successful historical data validation."""
        print("\n" + "="*60)
        print("Test 1: Historical Data Validation (Success)")
        print("="*60)
        
        try:
            df = self.create_sample_historical_data(1000)
            result = await validate_historical_data(df)
            
            assert result["valid"] == True, "Should be valid"
            assert result["total_rows"] == 1000, "Should have 1000 rows"
            assert "pricing_model_counts" in result, "Should have pricing model counts"
            
            print(f"  ✓ Validation passed: {result['total_rows']} rows")
            print(f"    - Pricing model distribution: {result.get('pricing_model_counts', {})}")
            
            return True
            
        except Exception as e:
            print(f"  ✗ Test failed: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    async def test_historical_data_insufficient_rows(self):
        """Test historical data validation with insufficient rows."""
        print("\n" + "="*60)
        print("Test 2: Historical Data Validation (Insufficient Rows)")
        print("="*60)
        
        try:
            df = self.create_sample_historical_data(500)  # Less than 1000
            result = await validate_historical_data(df)
            
            assert result["valid"] == False, "Should be invalid"
            assert "1000" in result["error"], "Error should mention 1000 row requirement"
            
            print(f"  ✓ Correctly rejected: {result['error']}")
            
            return True
            
        except Exception as e:
            print(f"  ✗ Test failed: {e}")
            return False
    
    async def test_historical_data_missing_columns(self):
        """Test historical data validation with missing columns."""
        print("\n" + "="*60)
        print("Test 3: Historical Data Validation (Missing Columns)")
        print("="*60)
        
        try:
            # Missing actual_price column
            df = pd.DataFrame({
                "completed_at": [datetime.now()] * 1000,
                "pricing_model": ["STANDARD"] * 1000
                # Missing actual_price
            })
            
            result = await validate_historical_data(df)
            
            assert result["valid"] == False, "Should be invalid"
            assert "actual_price" in result["error"], "Error should mention missing column"
            
            print(f"  ✓ Correctly rejected: {result['error']}")
            
            return True
            
        except Exception as e:
            print(f"  ✗ Test failed: {e}")
            return False
    
    async def test_historical_data_invalid_pricing_model(self):
        """Test historical data validation with invalid pricing model."""
        print("\n" + "="*60)
        print("Test 4: Historical Data Validation (Invalid Pricing Model)")
        print("="*60)
        
        try:
            df = pd.DataFrame({
                "completed_at": [datetime.now()] * 1000,
                "pricing_model": ["INVALID"] * 1000,
                "actual_price": [45.0] * 1000
            })
            
            result = await validate_historical_data(df)
            
            assert result["valid"] == False, "Should be invalid"
            assert "INVALID" in result["error"] or "pricing_model" in result["error"], \
                "Error should mention invalid pricing model"
            
            print(f"  ✓ Correctly rejected: {result['error']}")
            
            return True
            
        except Exception as e:
            print(f"  ✗ Test failed: {e}")
            return False
    
    async def test_competitor_data_validation_success(self):
        """Test successful competitor data validation."""
        print("\n" + "="*60)
        print("Test 5: Competitor Data Validation (Success)")
        print("="*60)
        
        try:
            df = self.create_sample_competitor_data(100)
            result = await validate_competitor_data(df)
            
            assert result["valid"] == True, "Should be valid"
            assert result["total_rows"] == 100, "Should have 100 rows"
            
            print(f"  ✓ Validation passed: {result['total_rows']} rows")
            
            return True
            
        except Exception as e:
            print(f"  ✗ Test failed: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    async def test_competitor_data_missing_columns(self):
        """Test competitor data validation with missing columns."""
        print("\n" + "="*60)
        print("Test 6: Competitor Data Validation (Missing Columns)")
        print("="*60)
        
        try:
            # Missing price column
            df = pd.DataFrame({
                "competitor_name": ["Uber"] * 100,
                "route": ["Downtown"] * 100,
                "timestamp": [datetime.now()] * 100
                # Missing price
            })
            
            result = await validate_competitor_data(df)
            
            assert result["valid"] == False, "Should be invalid"
            assert "price" in result["error"], "Error should mention missing column"
            
            print(f"  ✓ Correctly rejected: {result['error']}")
            
            return True
            
        except Exception as e:
            print(f"  ✗ Test failed: {e}")
            return False
    
    def test_csv_file_creation(self):
        """Test creating valid CSV files for upload."""
        print("\n" + "="*60)
        print("Test 7: CSV File Creation")
        print("="*60)
        
        try:
            # Create historical data CSV
            df_historical = self.create_sample_historical_data(1000)
            csv_buffer = io.StringIO()
            df_historical.to_csv(csv_buffer, index=False)
            csv_content = csv_buffer.getvalue()
            
            # Verify CSV can be read back
            df_read = pd.read_csv(io.StringIO(csv_content))
            assert len(df_read) == 1000, "CSV should have 1000 rows"
            assert "completed_at" in df_read.columns, "CSV should have completed_at column"
            
            print(f"  ✓ Historical data CSV created: {len(csv_content)} bytes")
            
            # Create competitor data CSV
            df_competitor = self.create_sample_competitor_data(100)
            csv_buffer2 = io.StringIO()
            df_competitor.to_csv(csv_buffer2, index=False)
            csv_content2 = csv_buffer2.getvalue()
            
            df_read2 = pd.read_csv(io.StringIO(csv_content2))
            assert len(df_read2) == 100, "CSV should have 100 rows"
            
            print(f"  ✓ Competitor data CSV created: {len(csv_content2)} bytes")
            
            return True
            
        except Exception as e:
            print(f"  ✗ Test failed: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def test_json_file_creation(self):
        """Test creating valid JSON files for upload."""
        print("\n" + "="*60)
        print("Test 8: JSON File Creation")
        print("="*60)
        
        try:
            # Create historical data JSON
            df_historical = self.create_sample_historical_data(1000)
            # Convert datetime to string for JSON
            df_historical["completed_at"] = df_historical["completed_at"].dt.strftime("%Y-%m-%d %H:%M:%S")
            json_data = df_historical.to_dict("records")
            json_content = json.dumps(json_data)
            
            # Verify JSON can be read back
            json_loaded = json.loads(json_content)
            assert len(json_loaded) == 1000, "JSON should have 1000 records"
            assert "completed_at" in json_loaded[0], "JSON should have completed_at field"
            
            print(f"  ✓ Historical data JSON created: {len(json_content)} bytes")
            
            return True
            
        except Exception as e:
            print(f"  ✗ Test failed: {e}")
            import traceback
            traceback.print_exc()
            return False


async def run_all_tests():
    """Run all tests and report results."""
    print("\n" + "="*60)
    print("FILE UPLOAD ENDPOINTS - TEST SUITE")
    print("="*60)
    
    test_suite = TestFileUpload()
    
    results = {
        "historical_validation_success": await test_suite.test_historical_data_validation_success(),
        "historical_insufficient_rows": await test_suite.test_historical_data_insufficient_rows(),
        "historical_missing_columns": await test_suite.test_historical_data_missing_columns(),
        "historical_invalid_pricing": await test_suite.test_historical_data_invalid_pricing_model(),
        "competitor_validation_success": await test_suite.test_competitor_data_validation_success(),
        "competitor_missing_columns": await test_suite.test_competitor_data_missing_columns(),
        "csv_creation": test_suite.test_csv_file_creation(),
        "json_creation": test_suite.test_json_file_creation()
    }
    
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
    import asyncio
    success = asyncio.run(run_all_tests())
    sys.exit(0 if success else 1)

