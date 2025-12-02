#!/usr/bin/env python3
"""
Script to verify Data Ingestion Agent has processed embeddings for historical data.

This script:
1. Checks MongoDB for historical_rides documents
2. Checks ChromaDB for corresponding embeddings
3. Verifies the connection between MongoDB documents and ChromaDB embeddings
"""

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
import chromadb
from chromadb.config import Settings as ChromaSettings
from app.config import settings

async def check_mongodb_data():
    """Check MongoDB for historical_rides documents."""
    print("=" * 60)
    print("Checking MongoDB for Historical Data")
    print("=" * 60)
    
    try:
        client = AsyncIOMotorClient(settings.mongodb_url)
        database = client[settings.mongodb_db_name]
        collection = database["historical_rides"]
        
        # Count documents
        count = await collection.count_documents({})
        print(f"✓ MongoDB Collection: historical_rides")
        print(f"  Total documents: {count}")
        
        if count == 0:
            print("  ⚠️  No historical data found in MongoDB")
            return []
        
        # Get sample documents
        sample_docs = await collection.find({}).limit(3).to_list(length=3)
        print(f"\n  Sample documents:")
        for i, doc in enumerate(sample_docs, 1):
            doc_id = str(doc.get("_id", "unknown"))
            order_date = doc.get("Order_Date", "N/A")
            cost = doc.get("Historical_Cost_of_Ride", "N/A")
            pricing_model = doc.get("Pricing_Model", "N/A")
            print(f"    {i}. ID: {doc_id[:24]}... | Date: {order_date} | Cost: ${cost} | Model: {pricing_model}")
        
        # Get all document IDs
        all_docs = await collection.find({}, {"_id": 1}).to_list(length=None)
        doc_ids = [str(doc["_id"]) for doc in all_docs]
        
        client.close()
        return doc_ids
        
    except Exception as e:
        print(f"✗ Error checking MongoDB: {e}")
        return []

def check_chromadb_embeddings():
    """Check ChromaDB for embeddings from historical_rides."""
    print("\n" + "=" * 60)
    print("Checking ChromaDB for Embeddings")
    print("=" * 60)
    
    try:
        # Connect to ChromaDB
        chroma_client = chromadb.PersistentClient(
            path=settings.CHROMADB_PATH,
            settings=ChromaSettings(anonymized_telemetry=False)
        )
        
        # Check which collection is used for historical_rides
        # Based on data_ingestion.py, historical_rides should go to "ride_scenarios_vectors"
        collection_name = "ride_scenarios_vectors"
        
        try:
            collection = chroma_client.get_collection(name=collection_name)
            count = collection.count()
            print(f"✓ ChromaDB Collection: {collection_name}")
            print(f"  Total embeddings: {count}")
            
            if count == 0:
                print("  ⚠️  No embeddings found in ChromaDB")
                return []
            
            # Get sample embeddings with metadata
            results = collection.peek(limit=5)
            print(f"\n  Sample embeddings:")
            for i, (embedding_id, metadata) in enumerate(zip(results['ids'], results['metadatas']), 1):
                mongodb_id = metadata.get('mongodb_id', 'N/A')
                source_collection = metadata.get('collection', 'N/A')
                description = metadata.get('description', 'N/A')[:50] + "..." if len(metadata.get('description', '')) > 50 else metadata.get('description', 'N/A')
                print(f"    {i}. ChromaDB ID: {embedding_id[:24]}...")
                print(f"       MongoDB ID: {mongodb_id[:24]}...")
                print(f"       Collection: {source_collection}")
                print(f"       Description: {description}")
            
            # Get all embeddings with metadata
            all_results = collection.get(limit=count)
            embeddings_data = []
            for i, metadata in enumerate(all_results['metadatas']):
                if metadata.get('collection') == 'historical_rides':
                    embeddings_data.append({
                        'chromadb_id': all_results['ids'][i],
                        'mongodb_id': metadata.get('mongodb_id'),
                        'description': metadata.get('description', '')
                    })
            
            print(f"\n  Embeddings from historical_rides: {len(embeddings_data)}")
            return embeddings_data
            
        except Exception as e:
            if "does not exist" in str(e) or "not found" in str(e):
                print(f"✗ Collection '{collection_name}' does not exist in ChromaDB")
                print("  → Data Ingestion Agent may not have run yet")
                return []
            else:
                raise
        
    except Exception as e:
        print(f"✗ Error checking ChromaDB: {e}")
        return []

def verify_connection(mongodb_ids, chromadb_embeddings):
    """Verify connection between MongoDB documents and ChromaDB embeddings."""
    print("\n" + "=" * 60)
    print("Verifying MongoDB ↔ ChromaDB Connection")
    print("=" * 60)
    
    if not mongodb_ids:
        print("⚠️  No MongoDB documents to verify")
        return
    
    if not chromadb_embeddings:
        print("⚠️  No ChromaDB embeddings to verify")
        print("\n  → Data Ingestion Agent may not have processed the data yet")
        print("  → Start the agent: cd backend && python app/agents/data_ingestion.py")
        return
    
    # Extract MongoDB IDs from ChromaDB embeddings
    chromadb_mongodb_ids = {emb['mongodb_id'] for emb in chromadb_embeddings if emb.get('mongodb_id')}
    mongodb_ids_set = set(mongodb_ids)
    
    # Find matches
    matched = mongodb_ids_set.intersection(chromadb_mongodb_ids)
    unmatched_mongo = mongodb_ids_set - chromadb_mongodb_ids
    unmatched_chroma = chromadb_mongodb_ids - mongodb_ids_set
    
    print(f"✓ Matched documents: {len(matched)} / {len(mongodb_ids)}")
    
    if unmatched_mongo:
        print(f"  ⚠️  {len(unmatched_mongo)} MongoDB documents without embeddings")
        if len(unmatched_mongo) <= 5:
            print(f"     IDs: {list(unmatched_mongo)[:5]}")
        else:
            print(f"     Sample IDs: {list(unmatched_mongo)[:5]}...")
    
    if unmatched_chroma:
        print(f"  ⚠️  {len(unmatched_chroma)} ChromaDB embeddings without matching MongoDB docs")
    
    if len(matched) == len(mongodb_ids) and len(mongodb_ids) > 0:
        print("\n  ✅ All MongoDB documents have corresponding embeddings!")
    elif len(matched) > 0:
        print(f"\n  ⚠️  Partial match: {len(matched)}/{len(mongodb_ids)} documents have embeddings")
    else:
        print("\n  ❌ No matches found - embeddings may not have been created yet")

async def main():
    """Main verification function."""
    print("\n" + "=" * 60)
    print("Data Ingestion Agent Verification")
    print("=" * 60)
    print("Checking if historical data has been processed into embeddings...")
    print()
    
    # Step 1: Check MongoDB
    mongodb_ids = await check_mongodb_data()
    
    # Step 2: Check ChromaDB
    chromadb_embeddings = check_chromadb_embeddings()
    
    # Step 3: Verify connection
    verify_connection(mongodb_ids, chromadb_embeddings)
    
    print("\n" + "=" * 60)
    print("Verification Complete")
    print("=" * 60)
    print("\nTo start the Data Ingestion Agent:")
    print("  cd backend && python app/agents/data_ingestion.py")
    print("\nOr use the start script (starts agent automatically):")
    print("  cd backend && ./start.sh")
    print("\nTo check agent logs:")
    print("  tail -f backend/logs/data_ingestion.log")
    print("  or")
    print("  ./backend/scripts/check_data_ingestion_logs.sh -f")
    print()

if __name__ == "__main__":
    asyncio.run(main())

