#!/usr/bin/env python3
"""
Quick test script for ML training endpoint.
Tests the /api/v1/ml/train endpoint and displays results.
"""
import requests
import json
import time

def test_train_endpoint():
    """Test the ML training endpoint."""
    url = "http://localhost:8000/api/v1/ml/train"
    
    print("=" * 60)
    print("Testing ML Training Endpoint")
    print("=" * 60)
    print(f"URL: {url}")
    print("Method: POST")
    print("\nSending request...\n")
    
    start_time = time.time()
    
    try:
        response = requests.post(url, timeout=120)
        elapsed = time.time() - start_time
        
        print(f"✓ Response received in {elapsed:.2f} seconds")
        print(f"Status Code: {response.status_code}")
        print("\nResponse Body:")
        print("-" * 60)
        
        if response.status_code == 200:
            data = response.json()
            print(json.dumps(data, indent=2))
            print("\n" + "=" * 60)
            print("✓ TRAINING SUCCESSFUL!")
            print("=" * 60)
            print(f"Model Path: {data.get('model_path', 'N/A')}")
            print(f"Training Rows: {data.get('training_rows', 'N/A')}")
            print(f"MAPE: {data.get('mape', 'N/A'):.4f}")
            print(f"Confidence: {data.get('confidence', 'N/A')}")
            
            if 'pricing_model_breakdown' in data:
                print("\nPricing Model Breakdown:")
                for model, count in data['pricing_model_breakdown'].items():
                    print(f"  - {model}: {count} rows")
        else:
            print(response.text)
            print("\n" + "=" * 60)
            print(f"✗ TRAINING FAILED (Status: {response.status_code})")
            print("=" * 60)
            
    except requests.exceptions.Timeout:
        elapsed = time.time() - start_time
        print(f"✗ Request timed out after {elapsed:.2f} seconds")
    except requests.exceptions.ConnectionError as e:
        print(f"✗ Connection error: {e}")
    except Exception as e:
        print(f"✗ Error: {e}")

if __name__ == "__main__":
    test_train_endpoint()


