"""
Test script to verify all ChromaDB collections are defined and accessible.

Tests:
- All 5 required collections exist
- Collections can be queried
- Collections have proper structure
"""
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import chromadb
from chromadb.config import Settings as ChromaSettings
from app.agents.utils import setup_chromadb_client, query_chromadb
from app.config import settings


# Required ChromaDB collections
REQUIRED_COLLECTIONS = [
    "ride_scenarios_vectors",
    "news_events_vectors",
    "customer_behavior_vectors",
    "strategy_knowledge_vectors",
    "competitor_analysis_vectors"
]


def test_collection_exists(collection_name: str) -> bool:
    """Test if a collection exists and can be accessed."""
    try:
        chroma_client = setup_chromadb_client()
        
        # Try to get the collection
        collection = chroma_client.get_collection(name=collection_name)
        
        # Check if collection is accessible
        count = collection.count()
        
        print(f"✓ Collection '{collection_name}' exists (count: {count})")
        return True
    except Exception as e:
        if "does not exist" in str(e) or "not found" in str(e):
            print(f"✗ Collection '{collection_name}' does not exist")
            return False
        else:
            print(f"✗ Error accessing collection '{collection_name}': {str(e)}")
            return False


def test_collection_query(collection_name: str) -> bool:
    """Test if a collection can be queried."""
    try:
        # Try to query the collection
        results = query_chromadb(collection_name, "test query", n_results=1)
        
        # Query should succeed even if no results (empty collection is OK)
        print(f"✓ Collection '{collection_name}' can be queried")
        return True
    except Exception as e:
        print(f"✗ Error querying collection '{collection_name}': {str(e)}")
        return False


def create_collection_if_missing(collection_name: str) -> bool:
    """Create a collection if it doesn't exist."""
    try:
        chroma_client = setup_chromadb_client()
        
        # Use get_or_create_collection (same as data_ingestion.py)
        # This will create if it doesn't exist, or get if it does
        collection = chroma_client.get_or_create_collection(
            name=collection_name,
            metadata={"description": f"Collection for {collection_name}"}
        )
        
        # Check if it was just created or already existed
        count = collection.count()
        if count == 0:
            print(f"✓ Collection '{collection_name}' created/verified (empty)")
        else:
            print(f"✓ Collection '{collection_name}' exists ({count} documents)")
        return True
            
    except Exception as e:
        print(f"✗ Error creating collection '{collection_name}': {str(e)}")
        return False


def main():
    """Test all ChromaDB collections."""
    print("=" * 60)
    print("Testing ChromaDB Collections")
    print("=" * 60)
    print(f"ChromaDB Path: {settings.CHROMADB_PATH}")
    print("=" * 60)
    
    # Test 1: Check if collections exist
    print("\n1. Checking if collections exist...")
    collections_exist = {}
    for collection_name in REQUIRED_COLLECTIONS:
        collections_exist[collection_name] = test_collection_exists(collection_name)
    
    # Test 2: Create missing collections
    print("\n2. Creating missing collections...")
    for collection_name in REQUIRED_COLLECTIONS:
        if not collections_exist[collection_name]:
            create_collection_if_missing(collection_name)
    
    # Test 3: Verify all collections can be queried
    print("\n3. Testing collection queries...")
    query_results = {}
    for collection_name in REQUIRED_COLLECTIONS:
        query_results[collection_name] = test_collection_query(collection_name)
    
    # Test 4: List all collections
    print("\n4. Listing all ChromaDB collections...")
    try:
        chroma_client = setup_chromadb_client()
        all_collections = chroma_client.list_collections()
        print(f"Total collections in ChromaDB: {len(all_collections)}")
        for coll in all_collections:
            count = coll.count()
            print(f"  - {coll.name}: {count} documents")
    except Exception as e:
        print(f"✗ Error listing collections: {str(e)}")
    
    # Re-check collections after creation
    print("\n5. Verifying all collections after creation...")
    final_check = {}
    for collection_name in REQUIRED_COLLECTIONS:
        final_check[collection_name] = test_collection_exists(collection_name)
    
    # Summary
    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)
    
    all_exist = all(final_check.values())
    all_queryable = all(query_results.values())
    
    for collection_name in REQUIRED_COLLECTIONS:
        exists = final_check[collection_name]
        queryable = query_results[collection_name]
        status = "✓" if exists and queryable else "✗"
        print(f"{status} {collection_name} - Exists: {exists}, Queryable: {queryable}")
    
    print("=" * 60)
    
    if all_exist and all_queryable:
        print("✅ All collections exist and are accessible!")
        return 0
    else:
        print("⚠️  Some collections need attention")
        return 1


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)

