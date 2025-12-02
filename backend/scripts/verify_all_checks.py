#!/usr/bin/env python3
"""
Master Verification Script

Runs all verification checks from CURSOR_IDE_INSTRUCTIONS.md lines 850-886.
This is the comprehensive verification script for the entire project.
"""

import sys
import subprocess
from pathlib import Path

def run_verification_script(script_name, description):
    """Run a verification script and return results."""
    print(f"\n{'=' * 80}")
    print(f"{description}")
    print(f"{'=' * 80}")
    
    script_path = Path(__file__).parent / script_name
    
    if not script_path.exists():
        print(f"⚠️  Script not found: {script_name}")
        return False
    
    try:
        result = subprocess.run(
            [sys.executable, str(script_path)],
            capture_output=True,
            text=True,
            timeout=60
        )
        
        print(result.stdout)
        if result.stderr:
            print(result.stderr, file=sys.stderr)
        
        return result.returncode == 0
    except Exception as e:
        print(f"❌ Error running {script_name}: {e}")
        return False

def main():
    """Run all verification checks."""
    print("=" * 80)
    print("Master Verification Script")
    print("Based on CURSOR_IDE_INSTRUCTIONS.md lines 850-886")
    print("=" * 80)
    
    verifications = [
        ("verify_no_docker.py", "NO DOCKER Verification"),
        ("verify_prophet_ml.py", "Prophet ML Verification"),
        ("verify_6_agents.py", "6 AI Agents Verification"),
        ("verify_n8n_workflows.py", "n8n Workflows Verification"),
        ("verify_integration.py", "Integration Verification"),
    ]
    
    results = {}
    
    for script, description in verifications:
        results[description] = run_verification_script(script, description)
    
    # Print final summary
    print("\n" + "=" * 80)
    print("Final Verification Summary")
    print("=" * 80)
    
    passed = sum(1 for v in results.values() if v)
    total = len(results)
    
    for description, result in results.items():
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status}: {description}")
    
    print(f"\nTotal: {passed}/{total} verification suites passed")
    
    if passed == total:
        print("\n✅ All verifications passed!")
        return 0
    else:
        print("\n⚠️  Some verifications failed.")
        return 1

if __name__ == "__main__":
    exit(main())

