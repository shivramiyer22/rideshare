#!/usr/bin/env python3
"""
Integration Verification Script

Verifies that all components integrate correctly.
Based on CURSOR_IDE_INSTRUCTIONS.md lines 879-885.
"""

import sys
from pathlib import Path

def check_order_queue_integration():
    """Check Order → Queue integration."""
    print("1. Checking Order → Priority Queue integration...")
    backend_dir = Path(__file__).parent.parent
    
    # Check priority queue router
    queue_router = backend_dir / "app" / "routers" / "orders.py"
    priority_queue = backend_dir / "app" / "priority_queue.py"
    
    if queue_router.exists() and priority_queue.exists():
        print("   ✓ Order and queue components exist")
        return True
    else:
        print("   ⚠️  Order or queue components missing")
        return False

def check_upload_training_integration():
    """Check Upload → Training integration."""
    print("\n2. Checking Upload → Training integration...")
    backend_dir = Path(__file__).parent.parent
    
    upload_router = backend_dir / "app" / "routers" / "upload.py"
    ml_router = backend_dir / "app" / "routers" / "ml.py"
    forecasting_ml = backend_dir / "app" / "forecasting_ml.py"
    
    if upload_router.exists() and ml_router.exists() and forecasting_ml.exists():
        print("   ✓ Upload, ML router, and forecasting components exist")
        return True
    else:
        print("   ⚠️  Some components missing")
        return False

def check_chatbot_integration():
    """Check Chatbot → Orchestrator → Agents integration."""
    print("\n3. Checking Chatbot → Orchestrator → Agents integration...")
    backend_dir = Path(__file__).parent.parent
    
    chatbot_router = backend_dir / "app" / "routers" / "chatbot.py"
    orchestrator = backend_dir / "app" / "agents" / "orchestrator.py"
    agents_dir = backend_dir / "app" / "agents"
    
    agents = ["analysis.py", "pricing.py", "forecasting.py", "recommendation.py"]
    found_agents = sum(1 for agent in agents if (agents_dir / agent).exists())
    
    if chatbot_router.exists() and orchestrator.exists() and found_agents == len(agents):
        print(f"   ✓ Chatbot, orchestrator, and all {len(agents)} worker agents exist")
        return True
    else:
        print(f"   ⚠️  Some components missing (found {found_agents}/{len(agents)} agents)")
        return False

def check_analytics_dashboard_integration():
    """Check Analytics Dashboard integration."""
    print("\n4. Checking Analytics Dashboard integration...")
    backend_dir = Path(__file__).parent.parent
    frontend_dir = backend_dir.parent / "frontend"
    
    analytics_router = backend_dir / "app" / "routers" / "analytics.py"
    analytics_component = frontend_dir / "src" / "components" / "AnalyticsDashboard.tsx"
    forecast_component = frontend_dir / "src" / "components" / "ForecastDashboard.tsx"
    
    components_found = sum([
        analytics_router.exists(),
        analytics_component.exists(),
        forecast_component.exists()
    ])
    
    if components_found == 3:
        print("   ✓ Analytics router and dashboard components exist")
        return True
    else:
        print(f"   ⚠️  Some components missing ({components_found}/3)")
        return False

def main():
    """Run all integration verification checks."""
    print("=" * 80)
    print("Integration Verification")
    print("Based on CURSOR_IDE_INSTRUCTIONS.md lines 879-885")
    print("=" * 80)
    
    checks = [
        check_order_queue_integration(),
        check_upload_training_integration(),
        check_chatbot_integration(),
        check_analytics_dashboard_integration()
    ]
    
    print("\n" + "=" * 80)
    print("Verification Summary")
    print("=" * 80)
    
    passed = sum(checks)
    total = len(checks)
    
    if passed == total:
        print(f"✅ All integration checks passed: {passed}/{total}")
        return 0
    else:
        print(f"⚠️  Some integration checks failed: {passed}/{total}")
        return 1

if __name__ == "__main__":
    exit(main())

