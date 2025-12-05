#!/usr/bin/env python3
"""
Test script for the streaming chatbot endpoint.

This script tests the new /api/v1/chatbot/chat/stream endpoint
to verify that responses are streamed token by token.
"""
import requests
import json
import time

API_URL = "http://localhost:8000"

def test_streaming_chat():
    """Test the streaming chat endpoint."""
    print("=" * 60)
    print("Testing Streaming Chatbot Endpoint")
    print("=" * 60)
    print()
    
    # Test message
    test_message = "What are our top 3 revenue-generating segments?"
    
    print(f"Sending message: '{test_message}'")
    print()
    print("Streaming response:")
    print("-" * 60)
    
    # Send request to streaming endpoint
    url = f"{API_URL}/api/v1/chatbot/chat/stream"
    payload = {
        "message": test_message,
        "context": {
            "thread_id": f"test_stream_{int(time.time())}",
            "user_id": "test_user"
        }
    }
    
    try:
        response = requests.post(
            url,
            json=payload,
            stream=True,  # Enable streaming
            headers={"Content-Type": "application/json"}
        )
        
        if response.status_code != 200:
            print(f"❌ Error: HTTP {response.status_code}")
            print(response.text)
            return False
        
        # Read the stream
        full_response = ""
        token_count = 0
        start_time = time.time()
        
        for line in response.iter_lines():
            if line:
                line_str = line.decode('utf-8')
                
                # Parse SSE format (data: {...})
                if line_str.startswith('data: '):
                    try:
                        data = json.loads(line_str[6:])
                        
                        if 'error' in data:
                            print(f"\n❌ Error: {data['error']}")
                            return False
                        
                        if 'token' in data and not data.get('done', False):
                            token = data['token']
                            full_response += token
                            token_count += 1
                            
                            # Print token (simulating real-time display)
                            print(token, end='', flush=True)
                        
                        if data.get('done', False):
                            elapsed = time.time() - start_time
                            print("\n" + "-" * 60)
                            print()
                            print(f"✅ Stream complete!")
                            print(f"   Tokens received: {token_count}")
                            print(f"   Total length: {len(full_response)} characters")
                            print(f"   Time elapsed: {elapsed:.2f}s")
                            print(f"   Avg speed: {len(full_response)/elapsed:.1f} chars/sec")
                            
                            if 'context' in data:
                                print(f"   Thread ID: {data['context'].get('thread_id', 'N/A')}")
                            
                            return True
                            
                    except json.JSONDecodeError as e:
                        print(f"\n⚠️  JSON parse error: {e}")
                        print(f"   Line: {line_str}")
        
        print("\n⚠️  Stream ended without completion signal")
        return False
        
    except requests.exceptions.RequestException as e:
        print(f"❌ Connection error: {e}")
        return False
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return False


def test_non_streaming_chat():
    """Test the regular (non-streaming) chat endpoint for comparison."""
    print()
    print("=" * 60)
    print("Testing Regular (Non-Streaming) Chatbot Endpoint")
    print("=" * 60)
    print()
    
    test_message = "What is our average ride price?"
    
    print(f"Sending message: '{test_message}'")
    print()
    
    url = f"{API_URL}/api/v1/chatbot/chat"
    payload = {
        "message": test_message,
        "context": {
            "thread_id": f"test_regular_{int(time.time())}",
            "user_id": "test_user"
        }
    }
    
    try:
        start_time = time.time()
        response = requests.post(url, json=payload)
        elapsed = time.time() - start_time
        
        if response.status_code != 200:
            print(f"❌ Error: HTTP {response.status_code}")
            print(response.text)
            return False
        
        data = response.json()
        response_text = data.get('response', '')
        
        print("Response:")
        print("-" * 60)
        print(response_text)
        print("-" * 60)
        print()
        print(f"✅ Response received!")
        print(f"   Total length: {len(response_text)} characters")
        print(f"   Time elapsed: {elapsed:.2f}s")
        print(f"   Thread ID: {data.get('context', {}).get('thread_id', 'N/A')}")
        
        return True
        
    except requests.exceptions.RequestException as e:
        print(f"❌ Connection error: {e}")
        return False
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return False


if __name__ == "__main__":
    print()
    print("🤖 Chatbot Streaming Test Suite")
    print("=" * 60)
    print()
    
    # Check if backend is running
    try:
        health_response = requests.get(f"{API_URL}/health", timeout=5)
        if health_response.status_code != 200:
            print("❌ Backend is not healthy")
            exit(1)
        print("✅ Backend is running and healthy")
        print()
    except requests.exceptions.RequestException:
        print("❌ Cannot connect to backend at", API_URL)
        print("   Make sure the backend is running on port 8000")
        exit(1)
    
    # Run tests
    results = []
    
    # Test 1: Streaming endpoint
    streaming_result = test_streaming_chat()
    results.append(("Streaming Chat", streaming_result))
    
    # Test 2: Regular endpoint (for comparison)
    regular_result = test_non_streaming_chat()
    results.append(("Regular Chat", regular_result))
    
    # Summary
    print()
    print("=" * 60)
    print("Test Summary")
    print("=" * 60)
    for name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status} - {name}")
    
    print()
    all_passed = all(result for _, result in results)
    if all_passed:
        print("🎉 All tests passed!")
        exit(0)
    else:
        print("⚠️  Some tests failed")
        exit(1)
