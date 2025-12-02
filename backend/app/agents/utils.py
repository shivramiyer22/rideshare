"""
Shared utilities for AI agents - ChromaDB querying and MongoDB document fetching.

This module provides reusable functions that all AI agents use to:
1. Query ChromaDB for similar documents (fast similarity search)
2. Fetch full documents from MongoDB using mongodb_id (complete data)

Think of ChromaDB as a search engine - it finds similar past scenarios quickly.
Think of MongoDB as the library - it stores the complete documents.

The workflow:
1. Agent needs context about similar past scenarios
2. Query ChromaDB with a text description (e.g., "urban evening rush premium")
3. ChromaDB returns mongodb_ids of similar documents
4. Fetch full documents from MongoDB using those IDs
5. Agent uses the full documents for analysis/decisions

This pattern is called RAG (Retrieval-Augmented Generation):
- Retrieve: Find relevant past scenarios (ChromaDB)
- Augment: Get full details (MongoDB)
- Generate: Use the context to make decisions (AI agent)
"""

import logging
from typing import List, Dict, Any, Optional
import chromadb
from chromadb.config import Settings as ChromaSettings
from bson import ObjectId
from app.config import settings
from app.database import get_database

logger = logging.getLogger(__name__)

# Global ChromaDB client (cached for performance)
_chroma_client: Optional[chromadb.PersistentClient] = None


def setup_chromadb_client() -> chromadb.PersistentClient:
    """
    Connect to ChromaDB and return client.
    
    ChromaDB is like a search engine for past scenarios.
    It stores embeddings (vector representations) of documents,
    allowing us to find similar documents quickly using similarity search.
    
    Returns:
        ChromaDB PersistentClient instance
    """
    global _chroma_client
    
    if _chroma_client is None:
        try:
            # Connect to ChromaDB with persistent storage
            # This means data survives restarts - like saving files to disk
            _chroma_client = chromadb.PersistentClient(
                path=settings.CHROMADB_PATH,
                settings=ChromaSettings(anonymized_telemetry=False)
            )
            logger.info(f"Connected to ChromaDB at {settings.CHROMADB_PATH}")
        except Exception as e:
            logger.error(f"Failed to connect to ChromaDB: {e}")
            raise
    
    return _chroma_client


def query_chromadb(
    collection_name: str,
    query_text: str,
    n_results: int = 5,
    where: Optional[Dict[str, Any]] = None
) -> List[Dict[str, Any]]:
    """
    Query ChromaDB collection for similar documents.
    
    This is like a search engine - you provide a text query,
    and ChromaDB finds the most similar documents based on meaning.
    
    How it works:
    1. ChromaDB converts your query text to an embedding (vector of numbers)
    2. It compares this embedding to all stored embeddings
    3. It returns the most similar documents (based on cosine similarity)
    
    Example:
        query_chromadb("ride_scenarios_vectors", "urban evening rush premium", n_results=5)
        Returns: List of similar past ride scenarios
    
    Args:
        collection_name: Name of ChromaDB collection to query
            - "ride_scenarios_vectors": Past rides and scenarios
            - "news_events_vectors": Events and news from n8n
            - "customer_behavior_vectors": Customer patterns
            - "strategy_knowledge_vectors": Business rules and strategies
            - "competitor_analysis_vectors": Competitor pricing
        query_text: Text description to search for (e.g., "urban evening rush premium")
        n_results: Number of similar documents to return (default: 5)
        where: Optional metadata filter (e.g., {"pricing_model": "STANDARD"})
    
    Returns:
        List of dictionaries, each containing:
            - mongodb_id: ID to fetch full document from MongoDB
            - metadata: Document metadata (collection, date, etc.)
            - distance: Similarity score (lower = more similar, typically 0.0-2.0)
            - document: The text description stored in ChromaDB
    """
    try:
        # Get ChromaDB client
        chroma_client = setup_chromadb_client()
        
        # Get the collection
        collection = chroma_client.get_collection(name=collection_name)
        
        # Query for similar documents
        # ChromaDB will convert query_text to an embedding and find similar ones
        results = collection.query(
            query_texts=[query_text],
            n_results=n_results,
            where=where  # Optional metadata filter
        )
        
        # Format results for easy use
        formatted_results = []
        
        # ChromaDB returns results in a specific format
        # We need to extract the data and format it nicely
        if results and len(results.get("ids", [[]])) > 0:
            ids = results["ids"][0]  # First (and only) query result
            metadatas = results.get("metadatas", [[]])[0] if results.get("metadatas") else [{}] * len(ids)
            distances = results.get("distances", [[]])[0] if results.get("distances") else [0.0] * len(ids)
            documents = results.get("documents", [[]])[0] if results.get("documents") else [""] * len(ids)
            
            for i, doc_id in enumerate(ids):
                formatted_results.append({
                    "mongodb_id": metadatas[i].get("mongodb_id", doc_id) if i < len(metadatas) else doc_id,
                    "metadata": metadatas[i] if i < len(metadatas) else {},
                    "distance": distances[i] if i < len(distances) else 0.0,
                    "document": documents[i] if i < len(documents) else ""
                })
        
        logger.info(f"Query '{query_text[:50]}...' returned {len(formatted_results)} results from {collection_name}")
        
        return formatted_results
        
    except Exception as e:
        logger.error(f"Error querying ChromaDB collection {collection_name}: {e}")
        return []


async def fetch_mongodb_documents(
    mongodb_ids: List[str],
    collection_name: str
) -> List[Dict[str, Any]]:
    """
    Fetch full documents from MongoDB using mongodb_id list.
    
    After querying ChromaDB, we get mongodb_ids (like library call numbers).
    This function fetches the complete documents from MongoDB using those IDs.
    
    Why we need this:
    - ChromaDB stores embeddings (vector representations) - fast but incomplete
    - MongoDB stores full documents - complete but slower to search
    - We combine both: fast search (ChromaDB) + complete data (MongoDB)
    
    Example:
        mongodb_ids = ["507f1f77bcf86cd799439011", "507f191e810c19729de860ea"]
        documents = await fetch_mongodb_documents(mongodb_ids, "ride_orders")
        Returns: List of complete order documents with all fields
    
    Args:
        mongodb_ids: List of MongoDB document IDs (as strings)
        collection_name: Name of MongoDB collection to query
            - "ride_orders": Current ride orders
            - "historical_rides": Past rides (for Prophet ML training)
            - "events_data": Events from n8n (Eventbrite)
            - "traffic_data": Traffic data from n8n (Google Maps)
            - "news_articles": News articles from n8n (NewsAPI)
            - "competitor_prices": Competitor pricing data
    
    Returns:
        List of complete MongoDB documents (dictionaries with all fields)
    """
    try:
        # Get database connection
        database = get_database()
        if database is None:
            logger.error("Database connection not available")
            return []
        
        # Get the MongoDB collection
        collection = database[collection_name]
        
        # Convert string IDs to ObjectId (MongoDB's ID format)
        # MongoDB uses ObjectId, not plain strings
        object_ids = []
        for doc_id in mongodb_ids:
            try:
                # Try to convert to ObjectId
                object_ids.append(ObjectId(doc_id))
            except Exception:
                # If conversion fails, skip this ID
                logger.warning(f"Invalid MongoDB ID format: {doc_id}")
                continue
        
        if not object_ids:
            logger.warning("No valid MongoDB IDs to fetch")
            return []
        
        # Fetch documents using $in operator (finds all documents with IDs in the list)
        cursor = collection.find({"_id": {"$in": object_ids}})
        documents = await cursor.to_list(length=None)
        
        # Convert ObjectId to string for JSON serialization
        # ObjectId is not JSON-serializable, so we convert it
        for doc in documents:
            if "_id" in doc:
                doc["_id"] = str(doc["_id"])
        
        logger.info(f"Fetched {len(documents)} documents from MongoDB collection {collection_name}")
        
        return documents
        
    except Exception as e:
        logger.error(f"Error fetching MongoDB documents from {collection_name}: {e}")
        return []


def format_documents_as_context(documents: List[Dict[str, Any]]) -> str:
    """
    Format MongoDB documents as a readable context string for AI agents.
    
    AI agents need context in text format to understand past scenarios.
    This function converts structured documents (dictionaries) into
    a readable text description.
    
    Example:
        documents = [
            {"customer": {"name": "John", "loyalty_tier": "Gold"}, "price": 45.50},
            {"customer": {"name": "Jane", "loyalty_tier": "Silver"}, "price": 32.00}
        ]
        Returns: "Document 1: Customer John (Gold tier), price $45.50. Document 2: Customer Jane (Silver tier), price $32.00."
    
    Args:
        documents: List of MongoDB documents (dictionaries)
    
    Returns:
        Formatted text string describing the documents
    """
    if not documents:
        return "No relevant documents found."
    
    context_parts = []
    for i, doc in enumerate(documents, 1):
        # Create a readable description of each document
        # Include key fields that are relevant for agents
        doc_str = f"Document {i}: "
        
        # Add relevant fields based on document structure
        if "customer" in doc:
            customer = doc["customer"]
            if isinstance(customer, dict):
                name = customer.get("name", "Unknown")
                tier = customer.get("loyalty_tier", "")
                doc_str += f"Customer {name}"
                if tier:
                    doc_str += f" ({tier} tier)"
                doc_str += ". "
        
        if "origin" in doc and "destination" in doc:
            doc_str += f"Route: {doc.get('origin')} → {doc.get('destination')}. "
        
        if "pricing_model" in doc:
            doc_str += f"Pricing: {doc.get('pricing_model')}. "
        
        if "actual_price" in doc or "price" in doc or "final_price" in doc:
            price = doc.get("actual_price") or doc.get("price") or doc.get("final_price")
            if price:
                doc_str += f"Price: ${price:.2f}. "
        
        if "completed_at" in doc or "date" in doc or "event_date" in doc:
            date = doc.get("completed_at") or doc.get("date") or doc.get("event_date")
            if date:
                doc_str += f"Date: {date}. "
        
        if "venue" in doc or "location" in doc:
            location = doc.get("venue") or doc.get("location")
            if location:
                doc_str += f"Location: {location}. "
        
        if "title" in doc:
            doc_str += f"Title: {doc.get('title')}. "
        
        if "summary" in doc or "description" in doc:
            summary = doc.get("summary") or doc.get("description", "")
            if summary:
                # Truncate long summaries
                summary = summary[:200] + "..." if len(summary) > 200 else summary
                doc_str += f"Summary: {summary}. "
        
        context_parts.append(doc_str.strip())
    
    return " ".join(context_parts)


