"""
Test script for agent utilities (ChromaDB and MongoDB functions).

Tests:
- setup_chromadb_client()
- query_chromadb()
- fetch_mongodb_documents()
- format_documents_as_context()
"""
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import pytest
import asyncio
from app.agents.utils import (
    setup_chromadb_client,
    query_chromadb,
    fetch_mongodb_documents,
    format_documents_as_context
)
from app.database import connect_to_mongo, get_database
from bson import ObjectId


class TestAgentUtils:
    """Test agent utility functions."""
    
    def test_setup_chromadb_client(self):
        """Test ChromaDB client setup."""
        try:
            client = setup_chromadb_client()
            assert client is not None
            print("✓ ChromaDB client setup successful")
            return True
        except Exception as e:
            print(f"✗ ChromaDB client setup failed: {str(e)}")
            return False
    
    def test_query_chromadb_empty_collection(self):
        """Test querying ChromaDB with empty collection."""
        try:
            # Query a collection that might be empty
            results = query_chromadb("ride_scenarios_vectors", "test query", n_results=5)
            # Should return empty list if collection is empty, not raise error
            assert isinstance(results, list)
            print("✓ ChromaDB query handles empty collections")
            return True
        except Exception as e:
            print(f"✗ ChromaDB query failed: {str(e)}")
            return False
    
    def test_query_chromadb_with_metadata_filter(self):
        """Test querying ChromaDB with metadata filter."""
        try:
            # Query with metadata filter
            results = query_chromadb(
                "ride_scenarios_vectors",
                "test query",
                n_results=5,
                where={"pricing_model": "STANDARD"}
            )
            assert isinstance(results, list)
            print("✓ ChromaDB query with metadata filter works")
            return True
        except Exception as e:
            print(f"✗ ChromaDB query with filter failed: {str(e)}")
            return False
    
    def test_fetch_mongodb_documents_empty_list(self):
        """Test fetching MongoDB documents with empty ID list."""
        async def run_test():
            try:
                # Test with empty list
                documents = await fetch_mongodb_documents([], "ride_orders")
                assert isinstance(documents, list)
                assert len(documents) == 0
                return True
            except Exception as e:
                print(f"✗ MongoDB fetch with empty list failed: {str(e)}")
                return False
        
        result = asyncio.run(run_test())
        if result:
            print("✓ MongoDB fetch handles empty ID list")
        return result
    
    def test_fetch_mongodb_documents_invalid_ids(self):
        """Test fetching MongoDB documents with invalid IDs."""
        async def run_test():
            try:
                # Test with invalid IDs
                documents = await fetch_mongodb_documents(["invalid_id_123"], "ride_orders")
                assert isinstance(documents, list)
                # Should return empty list for invalid IDs, not raise error
                return True
            except Exception as e:
                print(f"✗ MongoDB fetch with invalid IDs failed: {str(e)}")
                return False
        
        result = asyncio.run(run_test())
        if result:
            print("✓ MongoDB fetch handles invalid IDs gracefully")
        return result
    
    def test_format_documents_as_context_empty(self):
        """Test formatting empty document list."""
        try:
            result = format_documents_as_context([])
            assert isinstance(result, str)
            assert "No relevant documents found" in result
            print("✓ Format documents handles empty list")
            return True
        except Exception as e:
            print(f"✗ Format documents failed: {str(e)}")
            return False
    
    def test_format_documents_as_context_with_data(self):
        """Test formatting documents with actual data."""
        try:
            documents = [
                {
                    "customer": {"name": "John", "loyalty_tier": "Gold"},
                    "price": 45.50,
                    "origin": "Downtown",
                    "destination": "Airport"
                },
                {
                    "customer": {"name": "Jane", "loyalty_tier": "Silver"},
                    "price": 32.00
                }
            ]
            result = format_documents_as_context(documents)
            assert isinstance(result, str)
            assert len(result) > 0
            assert "John" in result or "Jane" in result
            print("✓ Format documents formats data correctly")
            return True
        except Exception as e:
            print(f"✗ Format documents with data failed: {str(e)}")
            return False


if __name__ == "__main__":
    print("=" * 60)
    print("Testing Agent Utilities")
    print("=" * 60)
    
    # Ensure MongoDB connection
    try:
        asyncio.run(connect_to_mongo())
    except Exception as e:
        print(f"Warning: Could not connect to MongoDB: {e}")
        print("Some tests may fail")
    
    test_instance = TestAgentUtils()
    
    tests = [
        ("ChromaDB client setup", test_instance.test_setup_chromadb_client),
        ("ChromaDB query empty collection", test_instance.test_query_chromadb_empty_collection),
        ("ChromaDB query with metadata filter", test_instance.test_query_chromadb_with_metadata_filter),
        ("MongoDB fetch empty list", test_instance.test_fetch_mongodb_documents_empty_list),
        ("MongoDB fetch invalid IDs", test_instance.test_fetch_mongodb_documents_invalid_ids),
        ("Format documents empty", test_instance.test_format_documents_as_context_empty),
        ("Format documents with data", test_instance.test_format_documents_as_context_with_data),
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



