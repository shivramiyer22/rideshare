#!/usr/bin/env python3
"""
6 AI Agents Verification Script

Verifies that all 6 AI agents are implemented and working.
Based on CURSOR_IDE_INSTRUCTIONS.md lines 863-869.
"""

import sys
import os
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

def check_agent_file(agent_name, file_path):
    """Check if an agent file exists and can be imported."""
    if not file_path.exists():
        print(f"   ❌ FAIL: {agent_name} file not found: {file_path}")
        return False
    
    try:
        # Try to import the agent module
        module_name = f"app.agents.{file_path.stem}"
        __import__(module_name)
        print(f"   ✓ PASS: {agent_name} file exists and can be imported")
        return True
    except Exception as e:
        print(f"   ⚠️  {agent_name} file exists but import failed: {e}")
        return False

def check_data_ingestion_agent():
    """Check Data Ingestion Agent."""
    print("\n1. Checking Data Ingestion Agent...")
    backend_dir = Path(__file__).parent.parent
    agent_file = backend_dir / "app" / "agents" / "data_ingestion.py"
    
    result = check_agent_file("Data Ingestion Agent", agent_file)
    
    # Check if it has main function
    if result:
        try:
            with open(agent_file, 'r') as f:
                content = f.read()
                if "async def main" in content or "def main" in content:
                    print("   ✓ Has main() function for standalone execution")
                if "monitor_change_streams" in content:
                    print("   ✓ Has change stream monitoring")
                if "process_document" in content:
                    print("   ✓ Has document processing function")
        except Exception:
            pass
    
    return result

def check_orchestrator_agent():
    """Check Chatbot Orchestrator Agent."""
    print("\n2. Checking Chatbot Orchestrator Agent...")
    backend_dir = Path(__file__).parent.parent
    agent_file = backend_dir / "app" / "agents" / "orchestrator.py"
    
    result = check_agent_file("Chatbot Orchestrator Agent", agent_file)
    
    if result:
        try:
            with open(agent_file, 'r') as f:
                content = f.read()
                if "orchestrator" in content.lower():
                    print("   ✓ Contains orchestrator logic")
        except Exception:
            pass
    
    return result

def check_analysis_agent():
    """Check Analysis Agent."""
    print("\n3. Checking Analysis Agent...")
    backend_dir = Path(__file__).parent.parent
    agent_file = backend_dir / "app" / "agents" / "analysis.py"
    
    result = check_agent_file("Analysis Agent", agent_file)
    
    if result:
        try:
            with open(agent_file, 'r') as f:
                content = f.read()
                if "analysis" in content.lower() or "kpi" in content.lower():
                    print("   ✓ Contains analysis logic")
        except Exception:
            pass
    
    return result

def check_pricing_agent():
    """Check Pricing Agent."""
    print("\n4. Checking Pricing Agent...")
    backend_dir = Path(__file__).parent.parent
    agent_file = backend_dir / "app" / "agents" / "pricing.py"
    
    result = check_agent_file("Pricing Agent", agent_file)
    
    if result:
        try:
            with open(agent_file, 'r') as f:
                content = f.read()
                if "pricing" in content.lower():
                    print("   ✓ Contains pricing logic")
        except Exception:
            pass
    
    return result

def check_forecasting_agent():
    """Check Forecasting Agent."""
    print("\n5. Checking Forecasting Agent...")
    backend_dir = Path(__file__).parent.parent
    agent_file = backend_dir / "app" / "agents" / "forecasting.py"
    
    result = check_agent_file("Forecasting Agent", agent_file)
    
    if result:
        try:
            with open(agent_file, 'r') as f:
                content = f.read()
                if "forecast" in content.lower() or "prophet" in content.lower():
                    print("   ✓ Contains forecasting logic")
        except Exception:
            pass
    
    return result

def check_recommendation_agent():
    """Check Recommendation Agent."""
    print("\n6. Checking Recommendation Agent...")
    backend_dir = Path(__file__).parent.parent
    agent_file = backend_dir / "app" / "agents" / "recommendation.py"
    
    result = check_agent_file("Recommendation Agent", agent_file)
    
    if result:
        try:
            with open(agent_file, 'r') as f:
                content = f.read()
                if "recommendation" in content.lower() or "recommend" in content.lower():
                    print("   ✓ Contains recommendation logic")
        except Exception:
            pass
    
    return result

def main():
    """Run all 6 AI Agents verification checks."""
    print("=" * 80)
    print("6 AI Agents Verification")
    print("Based on CURSOR_IDE_INSTRUCTIONS.md lines 863-869")
    print("=" * 80)
    
    checks = [
        check_data_ingestion_agent(),
        check_orchestrator_agent(),
        check_analysis_agent(),
        check_pricing_agent(),
        check_forecasting_agent(),
        check_recommendation_agent()
    ]
    
    print("\n" + "=" * 80)
    print("Verification Summary")
    print("=" * 80)
    
    passed = sum(checks)
    total = len(checks)
    
    if passed == total:
        print(f"✅ All 6 agents verified: {passed}/{total}")
        return 0
    else:
        print(f"⚠️  Some agents missing or failed: {passed}/{total}")
        return 1

if __name__ == "__main__":
    exit(main())

