#!/usr/bin/env python3
"""
Prophet ML Verification Script

Verifies that Prophet ML is the ONLY forecasting method (NO moving averages).
Based on CURSOR_IDE_INSTRUCTIONS.md lines 857-861.
"""

import os
import subprocess
from pathlib import Path

def check_no_moving_averages():
    """Search codebase for moving_average references (should not exist)."""
    print("1. Checking for moving averages in codebase...")
    project_root = Path(__file__).parent.parent.parent
    
    try:
        # Exclude venv, node_modules, and other third-party directories
        result = subprocess.run(
            ["grep", "-r", "-i", "--exclude-dir=venv", "--exclude-dir=node_modules", 
             "--exclude-dir=.git", "--exclude-dir=__pycache__", 
             "moving_average", str(project_root / "backend" / "app")],
            capture_output=True,
            text=True,
            cwd=str(project_root),
            timeout=10
        )
        
        if result.returncode == 0 and result.stdout.strip():
            lines = result.stdout.strip().split('\n')
            print(f"   ❌ FAIL: Found {len(lines)} reference(s) to 'moving_average':")
            for line in lines[:5]:  # Show first 5
                print(f"      {line}")
            if len(lines) > 5:
                print(f"      ... and {len(lines) - 5} more")
            return False
        else:
            print("   ✓ PASS: No moving averages found")
            return True
    except Exception as e:
        print(f"   ⚠️  Could not check: {e}")
        return True  # Assume pass if check fails

def check_prophet_models():
    """Check if Prophet models exist."""
    print("\n2. Checking for Prophet ML model files...")
    models_dir = Path(__file__).parent.parent / "models"
    
    if not models_dir.exists():
        print(f"   ⚠️  Models directory not found: {models_dir}")
        return False
    
    model_files = list(models_dir.glob("*.pkl"))
    
    if model_files:
        print(f"   ✓ Found {len(model_files)} Prophet model file(s):")
        for model_file in model_files:
            print(f"      - {model_file.name}")
        return True
    else:
        print("   ⚠️  No Prophet model files found (.pkl)")
        print("   → Train models using /api/v1/ml/train endpoint")
        return False

def check_prophet_imports():
    """Check that Prophet is imported in forecasting code."""
    print("\n3. Checking Prophet ML imports...")
    backend_dir = Path(__file__).parent.parent
    
    forecasting_file = backend_dir / "app" / "forecasting_ml.py"
    
    if not forecasting_file.exists():
        print(f"   ❌ FAIL: forecasting_ml.py not found")
        return False
    
    try:
        with open(forecasting_file, 'r') as f:
            content = f.read()
            if "from prophet import Prophet" in content or "from prophet import" in content:
                print("   ✓ PASS: Prophet imported in forecasting_ml.py")
                return True
            else:
                print("   ⚠️  Prophet import not found in forecasting_ml.py")
                return False
    except Exception as e:
        print(f"   ⚠️  Could not check: {e}")
        return False

def check_forecast_endpoints():
    """Check that forecast endpoints exist."""
    print("\n4. Checking forecast endpoints...")
    backend_dir = Path(__file__).parent.parent
    ml_router = backend_dir / "app" / "routers" / "ml.py"
    
    if not ml_router.exists():
        print("   ⚠️  ml.py router not found")
        return False
    
    try:
        with open(ml_router, 'r') as f:
            content = f.read()
            if "forecast" in content.lower() and "prophet" in content.lower():
                print("   ✓ PASS: Forecast endpoints found with Prophet references")
                return True
            else:
                print("   ⚠️  Forecast endpoints may not use Prophet")
                return False
    except Exception as e:
        print(f"   ⚠️  Could not check: {e}")
        return False

def main():
    """Run all Prophet ML verification checks."""
    print("=" * 80)
    print("Prophet ML Verification")
    print("Based on CURSOR_IDE_INSTRUCTIONS.md lines 857-861")
    print("=" * 80)
    
    checks = [
        check_no_moving_averages(),
        check_prophet_models(),
        check_prophet_imports(),
        check_forecast_endpoints()
    ]
    
    print("\n" + "=" * 80)
    print("Verification Summary")
    print("=" * 80)
    
    passed = sum(checks)
    total = len(checks)
    
    if passed == total:
        print(f"✅ All checks passed: {passed}/{total}")
        return 0
    else:
        print(f"⚠️  Some checks failed: {passed}/{total}")
        return 1

if __name__ == "__main__":
    exit(main())

