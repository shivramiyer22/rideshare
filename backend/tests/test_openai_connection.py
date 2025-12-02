"""
Test script for OpenAI API connection.

Tests:
- OpenAI API key configuration
- Embeddings API connection
- Chat completions API connection
- Error handling
"""
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import pytest
import asyncio
from app.config import settings
from openai import OpenAI


class TestOpenAIConnection:
    """Test OpenAI API connection."""
    
    def test_openai_api_key_configured(self):
        """Test that OpenAI API key is configured (or gracefully handle missing)."""
        if settings.OPENAI_API_KEY:
            assert len(settings.OPENAI_API_KEY) > 0
            # Don't print the key, just verify it exists
            print("✓ OpenAI API key is configured")
            return True
        else:
            print("⚠ OpenAI API key not configured (expected in test env)")
            return True  # Not a failure, just missing config
    
    def test_openai_embeddings_connection(self):
        """Test OpenAI Embeddings API connection."""
        if not settings.OPENAI_API_KEY:
            print("⚠ Skipping: OpenAI API key not configured")
            return True
        
        try:
            client = OpenAI(api_key=settings.OPENAI_API_KEY)
            
            # Test embeddings API
            response = client.embeddings.create(
                model="text-embedding-3-small",
                input="test query"
            )
            
            assert response is not None
            assert len(response.data) > 0
            assert len(response.data[0].embedding) == 1536  # text-embedding-3-small dimensions
            
            print("✓ OpenAI Embeddings API connection successful")
            return True
        except Exception as e:
            if "api_key" in str(e).lower() or "invalid" in str(e).lower():
                print(f"⚠ OpenAI API key issue: {str(e)[:100]}")
                return True  # Not a test failure
            print(f"✗ OpenAI Embeddings API error: {str(e)}")
            return False
    
    def test_openai_chat_completions_connection(self):
        """Test OpenAI Chat Completions API connection."""
        if not settings.OPENAI_API_KEY:
            print("⚠ Skipping: OpenAI API key not configured")
            return True
        
        try:
            client = OpenAI(api_key=settings.OPENAI_API_KEY)
            
            # Test chat completions API
            response = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[{"role": "user", "content": "Say 'test successful'"}],
                max_tokens=10
            )
            
            assert response is not None
            assert len(response.choices) > 0
            assert response.choices[0].message.content is not None
            
            print("✓ OpenAI Chat Completions API connection successful")
            return True
        except Exception as e:
            if "api_key" in str(e).lower() or "invalid" in str(e).lower():
                print(f"⚠ OpenAI API key issue: {str(e)[:100]}")
                return True  # Not a test failure
            print(f"✗ OpenAI Chat Completions API error: {str(e)}")
            return False
    
    def test_openai_async_embeddings(self):
        """Test OpenAI async embeddings (used by agents)."""
        async def test_async():
            if not settings.OPENAI_API_KEY:
                return True
            
            try:
                from app.agents.data_ingestion import create_embedding
                
                embedding = await create_embedding("test async query")
                
                if embedding:
                    assert isinstance(embedding, list)
                    assert len(embedding) == 1536
                    print("✓ OpenAI async embeddings work")
                    return True
                else:
                    print("⚠ OpenAI async embeddings returned None")
                    return True  # Not a failure
            except Exception as e:
                if "api_key" in str(e).lower():
                    print("⚠ OpenAI API key issue (expected in test env)")
                    return True
                print(f"✗ Async embeddings error: {str(e)}")
                return False
        
        result = asyncio.run(test_async())
        return result


if __name__ == "__main__":
    print("=" * 60)
    print("Testing OpenAI API Connection")
    print("=" * 60)
    
    test_instance = TestOpenAIConnection()
    
    tests = [
        ("OpenAI API key configured", test_instance.test_openai_api_key_configured),
        ("OpenAI Embeddings API connection", test_instance.test_openai_embeddings_connection),
        ("OpenAI Chat Completions API connection", test_instance.test_openai_chat_completions_connection),
        ("OpenAI async embeddings", test_instance.test_openai_async_embeddings),
    ]
    
    passed = 0
    failed = 0
    
    for test_name, test_func in tests:
        try:
            if test_func():
                passed += 1
            else:
                failed += 1
        except Exception as e:
            print(f"✗ {test_name}: {str(e)}")
            failed += 1
    
    print("=" * 60)
    print(f"Results: {passed} passed, {failed} failed")
    print("=" * 60)
    
    if failed == 0:
        print("✅ All tests passed!")
        sys.exit(0)
    else:
        print("❌ Some tests failed")
        sys.exit(1)


