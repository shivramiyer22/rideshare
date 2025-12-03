"""
Test script for Pricing Engine.

Tests:
1. CONTRACTED pricing (fixed price, no multipliers)
2. STANDARD pricing with all multipliers
3. CUSTOM pricing with all multipliers
4. Loyalty discounts (Gold, Silver, Regular)
5. Surge multiplier thresholds
6. Revenue score calculation
7. Breakdown structure validation

Run with: python -m pytest backend/tests/test_pricing_engine.py -v
Or: python backend/tests/test_pricing_engine.py
"""

import sys
from pathlib import Path

# Add backend to path
backend_path = Path(__file__).parent.parent
sys.path.insert(0, str(backend_path))

from app.pricing_engine import PricingEngine, PricingModel


class TestPricingEngine:
    """Test suite for Pricing Engine."""
    
    def __init__(self):
        """Initialize test suite."""
        self.engine = PricingEngine()
    
    def test_contracted_pricing(self):
        """Test CONTRACTED pricing (fixed price, no multipliers)."""
        print("\n" + "="*60)
        print("Test 1: CONTRACTED Pricing")
        print("="*60)
        
        try:
            order_data = {
                "pricing_model": "CONTRACTED",
                "fixed_price": 45.00,
                "customer": {"loyalty_tier": "Gold"}
            }
            
            result = self.engine.calculate_price(order_data)
            
            # Verify structure
            assert "final_price" in result, "Missing final_price"
            assert "breakdown" in result, "Missing breakdown"
            assert "revenue_score" in result, "Missing revenue_score"
            assert "pricing_model" in result, "Missing pricing_model"
            assert result["pricing_model"] == "CONTRACTED", "Wrong pricing_model"
            
            # Verify CONTRACTED has no multipliers
            multipliers = result["breakdown"]["multipliers"]
            assert multipliers["time_of_day"]["value"] == 1.0, "CONTRACTED should have no time multiplier"
            assert multipliers["location"]["value"] == 1.0, "CONTRACTED should have no location multiplier"
            assert multipliers["vehicle"]["value"] == 1.0, "CONTRACTED should have no vehicle multiplier"
            assert multipliers["surge"]["value"] == 1.0, "CONTRACTED should have no surge multiplier"
            
            # Verify loyalty discount applied
            discount = result["breakdown"]["loyalty_discount"]
            assert discount["percentage"] == 0.15, "Gold should have 15% discount"
            
            # Verify final price (45.00 - 15% = 38.25)
            expected_price = 45.00 * (1 - 0.15)
            assert abs(result["final_price"] - expected_price) < 0.01, f"Expected {expected_price}, got {result['final_price']}"
            
            print(f"  ✓ CONTRACTED pricing: ${result['final_price']}")
            print(f"    - Fixed price: ${order_data['fixed_price']}")
            print(f"    - Loyalty discount: {discount['percentage']*100}%")
            print(f"    - Revenue score: ${result['revenue_score']}")
            
            return True
            
        except Exception as e:
            print(f"  ✗ CONTRACTED pricing test failed: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def test_standard_pricing_with_multipliers(self):
        """Test STANDARD pricing with all multipliers."""
        print("\n" + "="*60)
        print("Test 2: STANDARD Pricing with Multipliers")
        print("="*60)
        
        try:
            order_data = {
                "pricing_model": "STANDARD",
                "distance": 10.0,
                "duration": 25.0,
                "time_of_day": "evening_rush",
                "location_type": "urban_high_demand",
                "vehicle_type": "premium",
                "supply_demand_ratio": 0.4,
                "customer": {"loyalty_tier": "Gold"}
            }
            
            result = self.engine.calculate_price(order_data)
            
            # Verify structure
            assert "final_price" in result, "Missing final_price"
            assert "breakdown" in result, "Missing breakdown"
            assert result["pricing_model"] == "STANDARD", "Wrong pricing_model"
            
            # Verify multipliers are applied
            multipliers = result["breakdown"]["multipliers"]
            assert multipliers["time_of_day"]["value"] == 1.4, "Evening rush should be 1.4x"
            assert multipliers["location"]["value"] == 1.3, "Urban high demand should be 1.3x"
            assert multipliers["vehicle"]["value"] == 1.6, "Premium vehicle should be 1.6x"
            assert multipliers["surge"]["value"] == 1.6, "Supply ratio 0.4 should be 1.6x surge"
            
            # Verify multiplier product
            expected_product = 1.4 * 1.3 * 1.6 * 1.6
            assert abs(result["breakdown"]["multiplier_product"] - expected_product) < 0.01, \
                f"Multiplier product mismatch"
            
            # Verify loyalty discount
            discount = result["breakdown"]["loyalty_discount"]
            assert discount["percentage"] == 0.15, "Gold should have 15% discount"
            
            # Verify revenue score is higher than final price (Gold bonus)
            assert result["revenue_score"] > result["final_price"], "Revenue score should include loyalty bonus"
            
            print(f"  ✓ STANDARD pricing: ${result['final_price']}")
            print(f"    - Base price: ${result['breakdown']['base_price']}")
            print(f"    - Multipliers: {result['breakdown']['multiplier_product']:.2f}x")
            print(f"    - Loyalty discount: {discount['percentage']*100}%")
            print(f"    - Revenue score: ${result['revenue_score']}")
            
            return True
            
        except Exception as e:
            print(f"  ✗ STANDARD pricing test failed: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def test_custom_pricing(self):
        """Test CUSTOM pricing with multipliers."""
        print("\n" + "="*60)
        print("Test 3: CUSTOM Pricing")
        print("="*60)
        
        try:
            order_data = {
                "pricing_model": "CUSTOM",
                "distance": 15.0,
                "duration": 30.0,
                "time_of_day": "regular",
                "location_type": "suburban",
                "vehicle_type": "economy",
                "supply_demand_ratio": 0.9,
                "customer": {"loyalty_tier": "Silver"}
            }
            
            result = self.engine.calculate_price(order_data)
            
            # Verify structure
            assert result["pricing_model"] == "CUSTOM", "Wrong pricing_model"
            
            # Verify CUSTOM has higher base rates than STANDARD
            # CUSTOM base_fare: 5.00, STANDARD: 4.00
            # CUSTOM rate_per_mile: 2.50, STANDARD: 2.00
            base_price = result["breakdown"]["base_price"]
            assert base_price > 0, "Base price should be positive"
            
            # Verify multipliers (all should be 1.0x for this test case)
            multipliers = result["breakdown"]["multipliers"]
            assert multipliers["time_of_day"]["value"] == 1.0, "Regular time should be 1.0x"
            assert multipliers["location"]["value"] == 1.0, "Suburban should be 1.0x"
            assert multipliers["vehicle"]["value"] == 1.0, "Economy should be 1.0x"
            assert multipliers["surge"]["value"] == 1.0, "Ratio 0.9 should be 1.0x (no surge)"
            
            # Verify Silver discount
            discount = result["breakdown"]["loyalty_discount"]
            assert discount["percentage"] == 0.10, "Silver should have 10% discount"
            
            print(f"  ✓ CUSTOM pricing: ${result['final_price']}")
            print(f"    - Base price: ${base_price}")
            print(f"    - Loyalty discount: {discount['percentage']*100}%")
            print(f"    - Revenue score: ${result['revenue_score']}")
            
            return True
            
        except Exception as e:
            print(f"  ✗ CUSTOM pricing test failed: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def test_surge_multiplier_thresholds(self):
        """Test surge multiplier at different thresholds."""
        print("\n" + "="*60)
        print("Test 4: Surge Multiplier Thresholds")
        print("="*60)
        
        test_cases = [
            (0.2, 2.0, "Very high demand"),
            (0.4, 1.6, "High demand"),
            (0.6, 1.3, "Moderate demand"),
            (0.9, 1.0, "Balanced")
        ]
        
        all_passed = True
        for ratio, expected_mult, description in test_cases:
            try:
                order_data = {
                    "pricing_model": "STANDARD",
                    "distance": 10.0,
                    "duration": 20.0,
                    "time_of_day": "regular",
                    "location_type": "suburban",
                    "vehicle_type": "economy",
                    "supply_demand_ratio": ratio,
                    "customer": {"loyalty_tier": "Regular"}
                }
                
                result = self.engine.calculate_price(order_data)
                surge_mult = result["breakdown"]["multipliers"]["surge"]["value"]
                
                assert abs(surge_mult - expected_mult) < 0.01, \
                    f"Ratio {ratio} should give {expected_mult}x, got {surge_mult}x"
                
                print(f"  ✓ Ratio {ratio}: {surge_mult}x surge ({description})")
                
            except Exception as e:
                print(f"  ✗ Ratio {ratio} test failed: {e}")
                all_passed = False
        
        return all_passed
    
    def test_loyalty_discounts(self):
        """Test loyalty discounts for Gold, Silver, Regular."""
        print("\n" + "="*60)
        print("Test 5: Loyalty Discounts")
        print("="*60)
        
        test_cases = [
            ("Gold", 0.15, "15% discount"),
            ("Silver", 0.10, "10% discount"),
            ("Regular", 0.0, "No discount")
        ]
        
        all_passed = True
        for tier, expected_discount, description in test_cases:
            try:
                order_data = {
                    "pricing_model": "STANDARD",
                    "distance": 10.0,
                    "duration": 20.0,
                    "time_of_day": "regular",
                    "location_type": "suburban",
                    "vehicle_type": "economy",
                    "supply_demand_ratio": 1.0,
                    "customer": {"loyalty_tier": tier}
                }
                
                result = self.engine.calculate_price(order_data)
                discount = result["breakdown"]["loyalty_discount"]
                
                assert abs(discount["percentage"] - expected_discount) < 0.01, \
                    f"{tier} should have {expected_discount*100}% discount, got {discount['percentage']*100}%"
                
                print(f"  ✓ {tier}: {description}")
                
            except Exception as e:
                print(f"  ✗ {tier} test failed: {e}")
                all_passed = False
        
        return all_passed
    
    def test_revenue_score_calculation(self):
        """Test revenue score calculation with loyalty bonuses."""
        print("\n" + "="*60)
        print("Test 6: Revenue Score Calculation")
        print("="*60)
        
        try:
            # Test Gold customer (should have 20% bonus)
            order_data_gold = {
                "pricing_model": "STANDARD",
                "distance": 10.0,
                "duration": 20.0,
                "time_of_day": "regular",
                "location_type": "suburban",
                "vehicle_type": "economy",
                "supply_demand_ratio": 1.0,
                "customer": {"loyalty_tier": "Gold"}
            }
            
            result_gold = self.engine.calculate_price(order_data_gold)
            expected_score_gold = result_gold["final_price"] * 1.2  # 20% bonus
            assert abs(result_gold["revenue_score"] - expected_score_gold) < 0.01, \
                f"Gold revenue score mismatch: expected {expected_score_gold}, got {result_gold['revenue_score']}"
            
            print(f"  ✓ Gold customer: final_price=${result_gold['final_price']}, revenue_score=${result_gold['revenue_score']}")
            
            # Test Regular customer (no bonus)
            order_data_regular = order_data_gold.copy()
            order_data_regular["customer"] = {"loyalty_tier": "Regular"}
            
            result_regular = self.engine.calculate_price(order_data_regular)
            assert abs(result_regular["revenue_score"] - result_regular["final_price"]) < 0.01, \
                "Regular customer revenue score should equal final_price"
            
            print(f"  ✓ Regular customer: final_price=${result_regular['final_price']}, revenue_score=${result_regular['revenue_score']}")
            
            # Verify Gold has higher revenue score
            assert result_gold["revenue_score"] > result_regular["revenue_score"], \
                "Gold customer should have higher revenue score"
            
            print(f"  ✓ Gold revenue score > Regular revenue score")
            
            return True
            
        except Exception as e:
            print(f"  ✗ Revenue score test failed: {e}")
            import traceback
            traceback.print_exc()
            return False


def run_all_tests():
    """Run all tests and report results."""
    print("\n" + "="*60)
    print("PRICING ENGINE - TEST SUITE")
    print("="*60)
    
    test_suite = TestPricingEngine()
    
    results = {
        "contracted_pricing": test_suite.test_contracted_pricing(),
        "standard_pricing": test_suite.test_standard_pricing_with_multipliers(),
        "custom_pricing": test_suite.test_custom_pricing(),
        "surge_thresholds": test_suite.test_surge_multiplier_thresholds(),
        "loyalty_discounts": test_suite.test_loyalty_discounts(),
        "revenue_score": test_suite.test_revenue_score_calculation()
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
    success = run_all_tests()
    sys.exit(0 if success else 1)



