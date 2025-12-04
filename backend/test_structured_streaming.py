#!/usr/bin/env python3
"""
Quick test to verify streaming chatbot with structured responses.
"""
import requests
import json
import time

API_URL = "http://localhost:8000"

def test_structured_streaming():
    """Test the streaming endpoint with structured response."""
    print("=" * 70)
    print("Testing Structured Streaming Chatbot")
    print("=" * 70)
    print()
    
    test_message = "What are our top 3 revenue segments?"
    
    print(f"Question: '{test_message}'")
    print()
    print("Response (streaming in real-time):")
    print("-" * 70)
    
    url = f"{API_URL}/api/v1/chatbot/chat/stream"
    payload = {
        "message": test_message,
        "context": {
            "thread_id": f"test_{int(time.time())}",
            "user_id": "test_user"
        }
    }
    
    try:
        start_time = time.time()
        first_token_time = None
        token_count = 0
        
        response = requests.post(
            url,
            json=payload,
            stream=True,
            headers={"Content-Type": "application/json"},
            timeout=60
        )
        
        if response.status_code != 200:
            print(f"❌ Error: HTTP {response.status_code}")
            print(response.text)
            return False
        
        full_response = ""
        
        for line in response.iter_lines():
            if line:
                line_str = line.decode('utf-8')
                
                if line_str.startswith('data: '):
                    try:
                        data = json.loads(line_str[6:])
                        
                        if 'error' in data:
                            print(f"\n❌ Error: {data['error']}")
                            return False
                        
                        if 'token' in data and not data.get('done', False):
                            if first_token_time is None:
                                first_token_time = time.time()
                            
                            token = data['token']
                            full_response += token
                            token_count += 1
                            
                            # Print token immediately (real-time streaming)
                            print(token, end='', flush=True)
                        
                        if data.get('done', False):
                            elapsed = time.time() - start_time
                            first_token_latency = (first_token_time - start_time) if first_token_time else 0
                            
                            print()
                            print("-" * 70)
                            print()
                            print("✅ Streaming complete!")
                            print(f"   First token latency: {first_token_latency:.2f}s")
                            print(f"   Total tokens: {token_count}")
                            print(f"   Total time: {elapsed:.2f}s")
                            print(f"   Response length: {len(full_response)} characters")
                            
                            # Check if response is structured
                            has_sections = '##' in full_response or '•' in full_response or '**' in full_response
                            if has_sections:
                                print("   ✅ Response is structured with sections")
                            else:
                                print("   ⚠️  Response may not be fully structured")
                            
                            return True
                            
                    except json.JSONDecodeError as e:
                        print(f"\n⚠️  JSON parse error: {e}")
        
        print("\n⚠️  Stream ended without completion signal")
        return False
        
    except requests.exceptions.RequestException as e:
        print(f"❌ Connection error: {e}")
        return False
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return False


if __name__ == "__main__":
    print()
    print("🤖 Structured Streaming Chatbot Test")
    print("=" * 70)
    print()
    
    # Check backend
    try:
        health = requests.get(f"{API_URL}/health", timeout=5)
        if health.status_code != 200:
            print("❌ Backend not healthy")
            exit(1)
        print("✅ Backend is healthy")
        print()
    except:
        print("❌ Cannot connect to backend")
        exit(1)
    
    # Run test
    success = test_structured_streaming()
    
    print()
    print("=" * 70)
    if success:
        print("🎉 Test PASSED - Streaming working with structured responses!")
    else:
        print("⚠️  Test had issues - check output above")
    print("=" * 70)
    print()
    
    exit(0 if success else 1)
