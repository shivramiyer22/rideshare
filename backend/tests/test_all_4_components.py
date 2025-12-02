"""
Master test script for all 4 components.

Runs all test suites to verify 100% pass rate:
1. Enhanced Pricing Agent
2. Enhanced Forecasting Agent
3. Enhanced Recommendation Agent
4. WebSocket Endpoint
"""
import sys
import os
import subprocess
import time

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

def run_test_script(script_name, description):
    """Run a test script and return results."""
    print(f"\n{'=' * 60}")
    print(f"Running: {description}")
    print(f"Script: {script_name}")
    print('=' * 60)
    
    script_path = os.path.join(os.path.dirname(__file__), script_name)
    
    try:
        result = subprocess.run(
            [sys.executable, script_path],
            capture_output=True,
            text=True,
            timeout=120
        )
        
        print(result.stdout)
        if result.stderr:
            # Filter out expected warnings
            stderr_lines = result.stderr.split('\n')
            filtered_stderr = [line for line in stderr_lines 
                             if line and not any(skip in line.lower() 
                               for skip in ['warning', 'info:', 'plotly', 'deprecation'])]
            if filtered_stderr:
                print("STDERR:", '\n'.join(filtered_stderr))
        
        return result.returncode == 0, result.stdout
    except subprocess.TimeoutExpired:
        print(f"✗ Test timed out: {script_name}")
        return False, "Timeout"
    except Exception as e:
        print(f"✗ Error running {script_name}: {str(e)}")
        return False, str(e)


def main():
    """Run all test suites."""
    print("=" * 60)
    print("COMPREHENSIVE TEST SUITE - All 4 Components")
    print("=" * 60)
    print(f"Python: {sys.version}")
    print(f"Working Directory: {os.getcwd()}")
    print("=" * 60)
    
    test_suites = [
        ("test_pricing_agent_enhanced.py", "Enhanced Pricing Agent"),
        ("test_forecasting_agent_enhanced.py", "Enhanced Forecasting Agent"),
        ("test_recommendation_agent_enhanced.py", "Enhanced Recommendation Agent"),
        ("test_websocket_endpoint.py", "WebSocket Endpoint"),
    ]
    
    results = {}
    total_passed = 0
    total_failed = 0
    
    for script_name, description in test_suites:
        passed, output = run_test_script(script_name, description)
        results[description] = {"passed": passed, "output": output}
        
        if passed:
            total_passed += 1
            print(f"\n✅ {description}: PASSED")
        else:
            total_failed += 1
            print(f"\n❌ {description}: FAILED")
    
    # Summary
    print("\n" + "=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)
    
    for description, result in results.items():
        status = "✅ PASSED" if result["passed"] else "❌ FAILED"
        print(f"{status}: {description}")
    
    print("=" * 60)
    print(f"Total: {total_passed} passed, {total_failed} failed")
    print("=" * 60)
    
    if total_failed == 0:
        print("\n🎉 ALL TESTS PASSED - 100% PASS RATE!")
        return 0
    else:
        print(f"\n⚠️  {total_failed} test suite(s) failed")
        return 1


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)


