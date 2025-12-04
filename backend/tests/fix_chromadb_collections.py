"""
Fix ChromaDB collections to use OpenAI embeddings (text-embedding-3-small, 1536 dimensions).

This script:
1. Deletes existing collections (if they use wrong embedding function)
2. Recreates them with OpenAI embedding function
3. Verifies they work correctly
"""
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import chromadb
from chromadb.config import Settings as ChromaSettings
from app.config import settings


def recreate_collections_with_openai():
    """Recreate all collections with OpenAI embedding function."""
    try:
        # Connect to ChromaDB
        chroma_client = chromadb.PersistentClient(
            path=settings.CHROMADB_PATH,
            settings=ChromaSettings(anonymized_telemetry=False)
        )
        
        # Required collections
        collections = [
            "ride_scenarios_vectors",
            "news_events_vectors",
            "customer_behavior_vectors",
            "strategy_knowledge_vectors",
            "competitor_analysis_vectors"
        ]
        
        print("=" * 60)
        print("Recreating ChromaDB Collections with OpenAI Embeddings")
        print("=" * 60)
        print(f"ChromaDB Path: {settings.CHROMADB_PATH}")
        print(f"OpenAI API Key: {'Configured' if settings.OPENAI_API_KEY else 'Not configured'}")
        print("=" * 60)
        
        # Setup OpenAI embedding function
        if not settings.OPENAI_API_KEY:
            print("⚠ OPENAI_API_KEY not configured. Collections will use default embeddings.")
            embedding_func = None
        else:
            try:
                from chromadb.utils.embedding_functions import OpenAIEmbeddingFunction
                embedding_func = OpenAIEmbeddingFunction(
                    api_key=settings.OPENAI_API_KEY,
                    model_name="text-embedding-3-small"
                )
                print("✓ Using OpenAI text-embedding-3-small (1536 dimensions)")
            except Exception as e:
                print(f"⚠ Could not setup OpenAI embedding function: {e}")
                print("  Collections will use default embeddings.")
                embedding_func = None
        
        print()
        
        # Delete and recreate each collection
        for collection_name in collections:
            try:
                # Try to delete existing collection
                try:
                    chroma_client.delete_collection(name=collection_name)
                    print(f"✓ Deleted existing collection: {collection_name}")
                except:
                    # Collection doesn't exist, that's OK
                    print(f"  Collection {collection_name} doesn't exist yet")
                
                # Create collection with OpenAI embedding function
                if embedding_func:
                    collection = chroma_client.create_collection(
                        name=collection_name,
                        embedding_function=embedding_func,
                        metadata={"description": f"Collection for {collection_name} with OpenAI embeddings"}
                    )
                else:
                    collection = chroma_client.create_collection(
                        name=collection_name,
                        metadata={"description": f"Collection for {collection_name}"}
                    )
                
                # Verify collection
                count = collection.count()
                print(f"✓ Created collection: {collection_name} ({count} documents)")
                
            except Exception as e:
                print(f"✗ Error recreating {collection_name}: {str(e)}")
                return False
        
        print("\n" + "=" * 60)
        print("✅ All collections recreated successfully!")
        print("=" * 60)
        
        # List all collections
        print("\nAll ChromaDB collections:")
        all_collections = chroma_client.list_collections()
        for coll in all_collections:
            count = coll.count()
            print(f"  - {coll.name}: {count} documents")
        
        return True
        
    except Exception as e:
        print(f"✗ Error: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = recreate_collections_with_openai()
    sys.exit(0 if success else 1)



