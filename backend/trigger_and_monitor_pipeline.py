"""
Trigger Pipeline and Monitor Execution
=======================================
This script triggers the pipeline via API and monitors execution
"""

import requests
import json
import time
from typing import Dict, Any

API_BASE = "http://localhost:8000/api/v1"


def trigger_pipeline():
    """Trigger the pipeline execution."""
    print("=" * 80)
    print("TRIGGERING PIPELINE")
    print("=" * 80)
    print()
    
    try:
        print("Sending trigger request (force=true)...")
        
        # Send POST with request body
        payload = {
            "force": True,
            "reason": "Manual validation test - checking 162 segments generation"
        }
        
        response = requests.post(
            f"{API_BASE}/pipeline/trigger", 
            json=payload,
            timeout=30
        )
        response.raise_for_status()
        result = response.json()
        
        print(f"✅ Pipeline triggered successfully!")
        print(f"   Run ID: {result.get('run_id')}")
        print(f"   Status: {result.get('status')}")
        print(f"   Message: {result.get('message')}")
        print()
        
        return result
    
    except requests.exceptions.Timeout:
        print("⏰ Request timed out (this is normal - pipeline runs in background)")
        print("   Pipeline is likely running. Use monitor script to check status.")
        print()
        return {"status": "triggered_timeout"}
    
    except requests.exceptions.RequestException as e:
        print(f"❌ Error triggering pipeline: {e}")
        return {"error": str(e)}


def check_pipeline_status():
    """Check current pipeline status."""
    print()
    print("=" * 80)
    print("CHECKING PIPELINE STATUS")
    print("=" * 80)
    print()
    
    try:
        response = requests.get(f"{API_BASE}/pipeline/status", timeout=10)
        response.raise_for_status()
        status = response.json()
        
        print(f"Is running: {status.get('is_running')}")
        print(f"Current run ID: {status.get('current_run_id')}")
        print(f"Current status: {status.get('current_status')}")
        print()
        
        return status
    
    except requests.exceptions.RequestException as e:
        print(f"❌ Error checking status: {e}")
        return {"error": str(e)}


def wait_for_completion(max_wait_seconds=300):
    """Wait for pipeline to complete."""
    print()
    print("=" * 80)
    print("WAITING FOR PIPELINE COMPLETION")
    print("=" * 80)
    print()
    
    start_time = time.time()
    check_interval = 5  # Check every 5 seconds
    
    while time.time() - start_time < max_wait_seconds:
        try:
            response = requests.get(f"{API_BASE}/pipeline/status", timeout=10)
            response.raise_for_status()
            status = response.json()
            
            is_running = status.get('is_running')
            current_status = status.get('current_status')
            
            elapsed = int(time.time() - start_time)
            print(f"[{elapsed}s] Status: {current_status} | Running: {is_running}")
            
            if not is_running:
                print()
                print("✅ Pipeline completed!")
                return True
            
            time.sleep(check_interval)
        
        except requests.exceptions.RequestException as e:
            print(f"❌ Error checking status: {e}")
            time.sleep(check_interval)
    
    print()
    print(f"⏰ Timeout after {max_wait_seconds}s")
    return False


if __name__ == "__main__":
    # Step 1: Trigger pipeline
    trigger_result = trigger_pipeline()
    
    if "error" in trigger_result:
        print("Failed to trigger pipeline. Exiting.")
        exit(1)
    
    # Step 2: Check initial status
    check_pipeline_status()
    
    # Step 3: Wait for completion
    print("Pipeline is running. Waiting for completion...")
    print("(This may take 2-5 minutes depending on data volume)")
    print()
    
    completed = wait_for_completion(max_wait_seconds=600)  # 10 minute timeout
    
    if completed:
        # Step 4: Check final status
        time.sleep(2)  # Give it a moment to save results
        final_status = check_pipeline_status()
        
        print()
        print("=" * 80)
        print("PIPELINE EXECUTION COMPLETE")
        print("=" * 80)
        print()
        print("Next step: Run validate_via_api.py to check results")
    else:
        print()
        print("Pipeline is still running or timed out.")
        print("You can check status manually or wait longer.")

