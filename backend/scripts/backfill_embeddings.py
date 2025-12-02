#!/usr/bin/env python3
"""
Script to backfill embeddings for existing MongoDB documents.

The Data Ingestion Agent only monitors change streams (new inserts/updates).
This script processes existing documents that were uploaded before the agent was running.
"""

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
from app.agents.data_ingestion import (
    setup_chromadb,
    process_document,
    generate_description
)
from app.config import settings

async def backfill_historical_rides():
    """Backfill embeddings for existing historical_rides documents."""
    print("=" * 60)
    print("Backfilling Embeddings for Historical Rides")
    print("=" * 60)
    
    try:
        # Step 1: Setup ChromaDB
        print("\nStep 1: Setting up ChromaDB...")
        chroma_client, chromadb_collections = setup_chromadb()
        print("✓ ChromaDB ready")
        
        # Step 2: Connect to MongoDB
        print("\nStep 2: Connecting to MongoDB...")
        mongo_client = AsyncIOMotorClient(settings.mongodb_url)
        database = mongo_client[settings.mongodb_db_name]
        collection = database["historical_rides"]
        
        # Test connection
        await mongo_client.admin.command('ping')
        print(f"✓ Connected to MongoDB: {settings.mongodb_db_name}")
        
        # Step 3: Count existing documents
        print("\nStep 3: Counting documents...")
        total_count = await collection.count_documents({})
        print(f"  Total documents in historical_rides: {total_count}")
        
        if total_count == 0:
            print("  ⚠️  No documents to process")
            return
        
        # Step 4: Process documents in batches
        print("\nStep 4: Processing documents...")
        batch_size = 100
        processed = 0
        failed = 0
        
        # Get collection name for ChromaDB
        chromadb_collection_name = "ride_scenarios_vectors"
        chromadb_collection = chromadb_collections.get(chromadb_collection_name)
        
        if not chromadb_collection:
            print(f"✗ ChromaDB collection '{chromadb_collection_name}' not found")
            return
        
        # Process in batches
        cursor = collection.find({})
        batch = []
        
        async for document in cursor:
            batch.append(document)
            
            if len(batch) >= batch_size:
                # Process batch
                for doc in batch:
                    try:
                        success = await process_document(
                            doc,
                            "historical_rides",
                            chromadb_collections
                        )
                        if success:
                            processed += 1
                        else:
                            failed += 1
                    except Exception as e:
                        print(f"  ⚠️  Error processing document {doc.get('_id')}: {e}")
                        failed += 1
                
                print(f"  Processed: {processed} | Failed: {failed} | Total: {processed + failed}/{total_count}")
                batch = []
        
        # Process remaining documents
        if batch:
            for doc in batch:
                try:
                    success = await process_document(
                        doc,
                        "historical_rides",
                        chromadb_collections
                    )
                    if success:
                        processed += 1
                    else:
                        failed += 1
                except Exception as e:
                    print(f"  ⚠️  Error processing document {doc.get('_id')}: {e}")
                    failed += 1
        
        print(f"\n✓ Processing complete!")
        print(f"  Successfully processed: {processed}")
        print(f"  Failed: {failed}")
        print(f"  Total: {processed + failed}/{total_count}")
        
        mongo_client.close()
        
    except Exception as e:
        print(f"\n✗ Error during backfill: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    print("\n" + "=" * 60)
    print("Embedding Backfill Script")
    print("=" * 60)
    print("This script will process existing MongoDB documents and create embeddings.")
    print("Note: This may take a while depending on the number of documents.")
    print()
    
    asyncio.run(backfill_historical_rides())
    
    print("\n" + "=" * 60)
    print("Backfill Complete")
    print("=" * 60)
    print("\nRun verification script to check results:")
    print("  python scripts/verify_embeddings.py")
    print()

