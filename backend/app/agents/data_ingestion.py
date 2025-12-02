"""
Data Ingestion Agent - Monitors MongoDB change streams and creates ChromaDB embeddings.

This agent is like a librarian who creates index cards for every new book (document) 
that arrives in the library (MongoDB). Other agents (Analysis, Pricing, Forecasting, 
Recommendation) will search these index cards (embeddings) to find relevant information.

How it works:
1. On startup: Processes all existing unprocessed documents in batches (minimal performance impact)
2. Continuously: Monitors MongoDB change streams for new documents (when n8n writes data, or new orders are created)
3. For each document: Generates a human-readable text description
4. Converts text to numbers (embeddings) using OpenAI API
5. Stores embeddings in ChromaDB with metadata (like a library call number)
6. Other agents query ChromaDB to find similar past scenarios

Key Features:
- Batch processing: Processes existing documents in batches of 50 with 1s delays
- Change stream monitoring: Real-time processing of new documents
- Automatic deduplication: Skips documents that already have embeddings
- Performance optimized: Batches and delays prevent system overload

This agent runs as a standalone process, not part of FastAPI.
"""

import asyncio
import logging
from datetime import datetime
from typing import Dict, List, Optional, Any
from motor.motor_asyncio import AsyncIOMotorClient
from bson import ObjectId
import chromadb
from chromadb.config import Settings as ChromaSettings
from openai import OpenAI
from app.config import settings

# Configure logging - helps us see what the agent is doing
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# ============================================================================
# CHROMADB SETUP
# ============================================================================

def setup_chromadb():
    """
    Create/connect to ChromaDB and ensure all 5 collections exist.
    
    Think of ChromaDB as 5 separate filing cabinets, each for different types of information:
    - ride_scenarios_vectors: Past rides and scenarios (used by Pricing & Analysis agents)
    - news_events_vectors: Events and news from n8n (used by Forecasting, Recommendation, Analysis agents)
    - customer_behavior_vectors: Customer patterns (used by Analysis & Recommendation agents)
    - strategy_knowledge_vectors: Business rules and strategies (used by Recommendation & Pricing agents)
    - competitor_analysis_vectors: Competitor pricing (used by Recommendation & Analysis agents)
    
    Other agents will query these collections to find similar past scenarios.
    """
    try:
        # Connect to ChromaDB with persistent storage
        # This means data survives restarts - like saving files to disk
        chroma_client = chromadb.PersistentClient(
            path=settings.CHROMADB_PATH,
            settings=ChromaSettings(anonymized_telemetry=False)
        )
        
        # Setup OpenAI embedding function (text-embedding-3-small, 1536 dimensions)
        # This is the same embedding model used in create_embedding()
        embedding_func = None
        if settings.OPENAI_API_KEY:
            try:
                from chromadb.utils.embedding_functions import OpenAIEmbeddingFunction
                embedding_func = OpenAIEmbeddingFunction(
                    api_key=settings.OPENAI_API_KEY,
                    model_name="text-embedding-3-small"
                )
                logger.info("Using OpenAI text-embedding-3-small for collections (1536 dimensions)")
            except Exception as e:
                logger.warning(f"Could not setup OpenAI embedding function: {e}. Using default.")
        else:
            logger.warning("OPENAI_API_KEY not configured. Collections will use default embeddings.")
        
        # Create or get the 5 collections
        # Each collection stores embeddings for a specific purpose
        # Use OpenAI embedding function if available
        
        # Collection 1: Ride scenarios - Pricing Agent and Analysis Agent will query this
        if embedding_func:
            ride_scenarios = chroma_client.get_or_create_collection(
                name="ride_scenarios_vectors",
                embedding_function=embedding_func,
                metadata={"description": "Past ride orders and historical rides for pattern matching"}
            )
        else:
            ride_scenarios = chroma_client.get_or_create_collection(
                name="ride_scenarios_vectors",
                metadata={"description": "Past ride orders and historical rides for pattern matching"}
            )
        logger.info("✓ ride_scenarios_vectors collection ready")
        
        # Collection 2: News and events - Forecasting, Recommendation, and Analysis agents use this
        # This is where n8n ingested events and news articles go
        if embedding_func:
            news_events = chroma_client.get_or_create_collection(
                name="news_events_vectors",
                embedding_function=embedding_func,
                metadata={"description": "Embeddings of n8n ingested events and news articles"}
            )
        else:
            news_events = chroma_client.get_or_create_collection(
                name="news_events_vectors",
                metadata={"description": "Embeddings of n8n ingested events and news articles"}
            )
        logger.info("✓ news_events_vectors collection ready")
        
        # Collection 3: Customer behavior - Analysis and Recommendation agents analyze this
        if embedding_func:
            customer_behavior = chroma_client.get_or_create_collection(
                name="customer_behavior_vectors",
                embedding_function=embedding_func,
                metadata={"description": "Customer segment behavioral patterns"}
            )
        else:
            customer_behavior = chroma_client.get_or_create_collection(
                name="customer_behavior_vectors",
                metadata={"description": "Customer segment behavioral patterns"}
            )
        logger.info("✓ customer_behavior_vectors collection ready")
        
        # Collection 4: Strategy knowledge - This is the PRIMARY RAG source for Recommendation Agent
        # Pricing Agent also uses this for business rules
        if embedding_func:
            strategy_knowledge = chroma_client.get_or_create_collection(
                name="strategy_knowledge_vectors",
                embedding_function=embedding_func,
                metadata={"description": "Pricing strategies and business rules (RAG source)"}
            )
        else:
            strategy_knowledge = chroma_client.get_or_create_collection(
                name="strategy_knowledge_vectors",
                metadata={"description": "Pricing strategies and business rules (RAG source)"}
            )
        logger.info("✓ strategy_knowledge_vectors collection ready")
        
        # Collection 5: Competitor analysis - Recommendation and Analysis agents use this
        if embedding_func:
            competitor_analysis = chroma_client.get_or_create_collection(
                name="competitor_analysis_vectors",
                embedding_function=embedding_func,
                metadata={"description": "Competitor pricing patterns from user uploads"}
            )
        else:
            competitor_analysis = chroma_client.get_or_create_collection(
                name="competitor_analysis_vectors",
                metadata={"description": "Competitor pricing patterns from user uploads"}
            )
        logger.info("✓ competitor_analysis_vectors collection ready")
        
        return chroma_client, {
            "ride_scenarios_vectors": ride_scenarios,
            "news_events_vectors": news_events,
            "customer_behavior_vectors": customer_behavior,
            "strategy_knowledge_vectors": strategy_knowledge,
            "competitor_analysis_vectors": competitor_analysis
        }
    except Exception as e:
        logger.error(f"Failed to setup ChromaDB: {e}")
        raise


# ============================================================================
# TEXT DESCRIPTION GENERATOR
# ============================================================================

def generate_description(document: Dict[str, Any], collection_name: str) -> str:
    """
    Generate a human-readable text description of a MongoDB document.
    
    Why this matters: Other agents will search for similar descriptions.
    A good description is like a good book title - it helps you find what you're looking for.
    
    The description should include:
    - Key details: dates, locations, types, amounts
    - Context: what happened, when, where
    - Searchable terms: things agents might look for
    
    Example: "Lakers playoff game Staples Center 20000 attendees Friday 7 PM"
    This is much better than just "Lakers game" because it has all the details.
    """
    try:
        if collection_name == "ride_orders":
            # For ride orders, include: location type, location, day, time, weather, vehicle type, customer tier
            # Exact format: "Urban downtown Friday evening rain premium Gold customer"
            # Extract location type (urban/suburban) from origin or location_type field
            location_type = document.get("location_type", "")
            if not location_type:
                # Infer from origin if available
                origin = str(document.get("origin", "")).lower()
                if "urban" in origin or "downtown" in origin or "city" in origin:
                    location_type = "Urban"
                elif "suburban" in origin:
                    location_type = "Suburban"
                else:
                    location_type = "Urban"  # Default
            
            # Get specific location
            origin = document.get("origin", "downtown")
            # Extract day of week if available
            day_of_week = document.get("day_of_week", "")
            if not day_of_week:
                # Try to extract from timestamp if available
                timestamp = document.get("created_at") or document.get("timestamp")
                if timestamp:
                    try:
                        from datetime import datetime
                        if isinstance(timestamp, str):
                            dt = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
                        else:
                            dt = timestamp
                        day_of_week = dt.strftime("%A")  # Monday, Tuesday, etc.
                    except:
                        day_of_week = "Friday"  # Default
                else:
                    day_of_week = "Friday"  # Default
            
            # Get time of day
            time_of_day = document.get("time_of_day", "evening")
            if "morning" in time_of_day.lower():
                time_of_day = "morning"
            elif "evening" in time_of_day.lower():
                time_of_day = "evening"
            elif "night" in time_of_day.lower():
                time_of_day = "night"
            else:
                time_of_day = "evening"  # Default
            
            # Get weather
            weather = document.get("weather", "rain")
            if not weather:
                weather = "rain"  # Default
            
            # Get vehicle type
            vehicle_type = document.get("vehicle_type", "premium")
            if vehicle_type.lower() not in ["premium", "economy"]:
                vehicle_type = "premium"  # Default
            
            # Get customer tier
            customer_tier = document.get("customer", {}).get("loyalty_tier", "Gold")
            if customer_tier not in ["Gold", "Silver", "Regular"]:
                customer_tier = "Gold"  # Default
            
            # Build description matching exact format: "Urban downtown Friday evening rain premium Gold customer"
            description = f"{location_type} {origin} {day_of_week} {time_of_day} {weather} {vehicle_type} {customer_tier} customer"
            return description
            
        elif collection_name == "events_data":
            # For events from n8n Eventbrite workflow
            # Exact format: "Lakers playoff game Staples Center 20000 attendees Friday 7 PM"
            event_name = document.get("event_name", document.get("name", "Unknown event"))
            venue = document.get("venue", document.get("location", document.get("venue_name", "Staples Center")))
            attendees = document.get("expected_attendees", document.get("attendees", document.get("capacity", "")))
            if not attendees:
                attendees = "20000"  # Default
            
            # Extract day of week
            event_date = document.get("event_date", document.get("date", document.get("start_date", "")))
            day_of_week = ""
            if event_date:
                try:
                    from datetime import datetime
                    if isinstance(event_date, str):
                        dt = datetime.fromisoformat(event_date.replace('Z', '+00:00'))
                    else:
                        dt = event_date
                    day_of_week = dt.strftime("%A")  # Monday, Tuesday, etc.
                except:
                    day_of_week = "Friday"  # Default
            else:
                day_of_week = "Friday"  # Default
            
            # Get time
            event_time = document.get("event_time", document.get("time", document.get("start_time", "7 PM")))
            if not event_time:
                event_time = "7 PM"  # Default
            
            # Build description matching exact format
            description = f"{event_name} {venue} {attendees} attendees {day_of_week} {event_time}"
            return description
            
        elif collection_name == "traffic_data":
            # For traffic data from n8n Google Maps workflow
            # Exact format: "Heavy traffic downtown to airport 45 min congestion"
            traffic_level = document.get("traffic_level", document.get("severity", "Heavy"))
            if not traffic_level or traffic_level.lower() not in ["heavy", "moderate", "light"]:
                traffic_level = "Heavy"  # Default
            
            origin = document.get("origin", "downtown")
            destination = document.get("destination", "airport")
            
            # Get duration in minutes
            duration_seconds = document.get("duration_seconds", document.get("duration", 0))
            if isinstance(duration_seconds, (int, float)):
                minutes = int(duration_seconds // 60) if duration_seconds > 60 else int(duration_seconds)
            else:
                minutes = 45  # Default
            
            # Build description matching exact format
            description = f"{traffic_level} traffic {origin} to {destination} {minutes} min congestion"
            return description
            
        elif collection_name == "news_articles":
            # For news articles from n8n NewsAPI workflow
            # Format: "{title} - {description}"
            title = document.get("title", "No title")
            description = document.get("description", document.get("summary", ""))
            
            if description:
                return f"{title} - {description}"
            return title
            
        elif collection_name == "customers":
            # For customer data
            # Example: "Gold customer from Los Angeles with 45 rides"
            loyalty_tier = document.get("loyalty_tier", "Regular")
            location = document.get("location", document.get("city", "unknown location"))
            ride_count = document.get("ride_count", document.get("total_rides", 0))
            
            return f"{loyalty_tier} customer from {location} with {ride_count} rides"
            
        elif collection_name == "historical_rides":
            # For historical rides uploaded by users (for Prophet ML training)
            # Similar to ride_orders but for historical data
            pricing_model = document.get("pricing_model", "STANDARD")
            completed_at = document.get("completed_at", document.get("date", ""))
            actual_price = document.get("actual_price", document.get("price", ""))
            
            return f"Historical {pricing_model} ride {completed_at} ${actual_price}"
            
        elif collection_name == "competitor_prices":
            # For competitor pricing data uploaded by users
            competitor = document.get("competitor_name", "competitor")
            route = document.get("route", "unknown route")
            price = document.get("price", "")
            timestamp = document.get("timestamp", document.get("date", ""))
            
            return f"{competitor} {route} ${price} {timestamp}"
            
        else:
            # Fallback: create description from document keys
            # This handles any other collection types
            key_fields = []
            for key in ["name", "title", "description", "type", "date", "location"]:
                if key in document:
                    key_fields.append(str(document[key]))
            return " ".join(key_fields) if key_fields else "Document from " + collection_name
            
    except Exception as e:
        logger.error(f"Error generating description for {collection_name}: {e}")
        return f"Document from {collection_name}"


# ============================================================================
# OPENAI EMBEDDINGS API
# ============================================================================

async def create_embedding(text: str, retries: int = 3) -> Optional[List[float]]:
    """
    Convert text to a vector (list of numbers) using OpenAI Embeddings API.
    
    Think of embeddings like this:
    - Text: "Lakers game Friday"
    - Embedding: [0.123, -0.456, 0.789, ...] (1536 numbers)
    
    Similar texts have similar numbers. This allows us to find similar documents
    by comparing the numbers (cosine similarity).
    
    Other agents will search for similar embeddings to find relevant context.
    
    Model: text-embedding-3-small (1536 dimensions)
    - Small = fast and cost-effective
    - 1536 dimensions = 1536 numbers to represent the text
    """
    if not settings.OPENAI_API_KEY:
        logger.error("OPENAI_API_KEY not found in environment variables")
        return None
    
    client = OpenAI(api_key=settings.OPENAI_API_KEY)
    
    for attempt in range(retries):
        try:
            response = client.embeddings.create(
                model="text-embedding-3-small",
                input=text
            )
            # Extract the embedding vector (list of 1536 numbers)
            embedding = response.data[0].embedding
            return embedding
        except Exception as e:
            if attempt < retries - 1:
                logger.warning(f"OpenAI API call failed (attempt {attempt + 1}/{retries}): {e}")
                await asyncio.sleep(2 ** attempt)  # Exponential backoff
            else:
                logger.error(f"Failed to create embedding after {retries} attempts: {e}")
                return None
    
    return None


# ============================================================================
# COLLECTION ROUTING LOGIC
# ============================================================================

def get_chromadb_collection_name(mongodb_collection: str) -> str:
    """
    Map MongoDB collection names to ChromaDB collection names.
    
    Each agent queries specific ChromaDB collections based on their needs:
    - Analysis Agent: ride_scenarios_vectors, news_events_vectors, customer_behavior_vectors, competitor_analysis_vectors
    - Pricing Agent: ride_scenarios_vectors, strategy_knowledge_vectors
    - Forecasting Agent: news_events_vectors (for n8n event context)
    - Recommendation Agent: strategy_knowledge_vectors (primary), news_events_vectors, competitor_analysis_vectors
    
    This routing ensures documents go to the right "filing cabinet" for agents to find them.
    """
    routing_map = {
        "ride_orders": "ride_scenarios_vectors",
        "historical_rides": "ride_scenarios_vectors",
        "events_data": "news_events_vectors",
        "news_articles": "news_events_vectors",
        "traffic_data": "news_events_vectors",  # Traffic is also event-related context
        "customers": "customer_behavior_vectors",
        "competitor_prices": "competitor_analysis_vectors"
    }
    
    return routing_map.get(mongodb_collection, "ride_scenarios_vectors")


# ============================================================================
# DOCUMENT PROCESSOR
# ============================================================================

async def process_document(
    document: Dict[str, Any],
    collection_name: str,
    chromadb_collections: Dict[str, Any]
) -> bool:
    """
    Process a single document: generate description, create embedding, store in ChromaDB.
    
    This is the core function that:
    1. Generates a text description (like a book title)
    2. Creates an embedding (converts text to numbers)
    3. Stores in ChromaDB with metadata (like a library card with call number)
    
    CRITICAL: The mongodb_id in metadata is essential!
    - Other agents will query ChromaDB and get back mongodb_id
    - They use mongodb_id to fetch the full document from MongoDB
    - This is like a library call number - it tells you where to find the full book
    """
    try:
        # Step 1: Generate human-readable description
        description = generate_description(document, collection_name)
        if not description or len(description.strip()) == 0:
            logger.warning(f"Empty description for document in {collection_name}, skipping")
            return False
        
        # Step 2: Create embedding using OpenAI API
        # This converts text to numbers that represent meaning
        embedding = await create_embedding(description)
        if embedding is None:
            logger.error(f"Failed to create embedding for document in {collection_name}")
            return False
        
        # Step 3: Determine which ChromaDB collection to use
        chromadb_collection_name = get_chromadb_collection_name(collection_name)
        chromadb_collection = chromadb_collections.get(chromadb_collection_name)
        
        if not chromadb_collection:
            logger.error(f"ChromaDB collection {chromadb_collection_name} not found")
            return False
        
        # Step 4: Prepare metadata
        # CRITICAL: mongodb_id is required - other agents use this to fetch full documents
        metadata = {
            "mongodb_id": str(document.get("_id", "")),
            "collection": collection_name,
            "timestamp": datetime.utcnow().isoformat(),
            "description": description[:200]  # Truncate for storage
        }
        
        # Add relevant fields for filtering (agents can filter by these)
        if "date" in document or "event_date" in document or "completed_at" in document:
            metadata["date"] = str(document.get("date") or document.get("event_date") or document.get("completed_at"))
        if "location" in document or "venue" in document:
            metadata["location"] = str(document.get("location") or document.get("venue", ""))
        if "pricing_model" in document:
            metadata["pricing_model"] = document["pricing_model"]
        if "loyalty_tier" in document:
            metadata["loyalty_tier"] = document["loyalty_tier"]
        
        # Step 5: Store in ChromaDB
        # The ID is the mongodb_id so we can easily find it later
        chromadb_collection.add(
            ids=[str(document.get("_id", ""))],
            embeddings=[embedding],
            metadatas=[metadata],
            documents=[description]  # Store the description text too
        )
        
        logger.info(f"✓ Created embedding for {collection_name} document: {document.get('_id')}")
        
        # Log which agent will use this collection
        agent_usage = {
            "ride_scenarios_vectors": "Pricing Agent, Analysis Agent",
            "news_events_vectors": "Forecasting Agent, Recommendation Agent, Analysis Agent",
            "customer_behavior_vectors": "Analysis Agent, Recommendation Agent",
            "strategy_knowledge_vectors": "Recommendation Agent (primary), Pricing Agent",
            "competitor_analysis_vectors": "Recommendation Agent, Analysis Agent"
        }
        logger.debug(f"  → This embedding will be queried by: {agent_usage.get(chromadb_collection_name, 'Unknown')}")
        
        return True
        
    except Exception as e:
        logger.error(f"Error processing document from {collection_name}: {e}")
        return False


# ============================================================================
# BATCH PROCESSING FOR EXISTING DOCUMENTS
# ============================================================================

async def get_processed_document_ids(
    chromadb_collection: Any,
    collection_name: str
) -> set:
    """
    Get all MongoDB document IDs that already have embeddings in ChromaDB.
    
    This helps us identify which documents need processing.
    """
    try:
        # Get all embeddings from this collection
        # We use get() with limit=None to get all documents
        # But ChromaDB has a default limit, so we'll use a large number
        all_results = chromadb_collection.get(
            where={"collection": collection_name},
            limit=100000  # Large limit to get all
        )
        
        # Extract MongoDB IDs from metadata
        processed_ids = set()
        if all_results and all_results.get('metadatas'):
            for metadata in all_results['metadatas']:
                mongodb_id = metadata.get('mongodb_id')
                if mongodb_id:
                    processed_ids.add(mongodb_id)
        
        return processed_ids
    except Exception as e:
        logger.warning(f"Error getting processed document IDs from ChromaDB: {e}")
        return set()


async def process_unprocessed_documents(
    database: Any,
    collection_name: str,
    chromadb_collections: Dict[str, Any],
    batch_size: int = 50,
    delay_between_batches: float = 1.0
) -> tuple[int, int]:
    """
    Process existing MongoDB documents that don't have embeddings yet.
    
    This function:
    1. Gets all document IDs from MongoDB
    2. Gets all processed document IDs from ChromaDB
    3. Finds unprocessed documents
    4. Processes them in batches with delays to minimize performance impact
    
    Args:
        database: MongoDB database instance
        collection_name: Name of MongoDB collection to process
        chromadb_collections: Dictionary of ChromaDB collections
        batch_size: Number of documents to process per batch
        delay_between_batches: Seconds to wait between batches
        
    Returns:
        Tuple of (processed_count, failed_count)
    """
    try:
        logger.info(f"Checking {collection_name} for unprocessed documents...")
        
        # Get ChromaDB collection for this MongoDB collection
        chromadb_collection_name = get_chromadb_collection_name(collection_name)
        chromadb_collection = chromadb_collections.get(chromadb_collection_name)
        
        if not chromadb_collection:
            logger.warning(f"ChromaDB collection {chromadb_collection_name} not found, skipping {collection_name}")
            return (0, 0)
        
        # Get MongoDB collection
        mongo_collection = database[collection_name]
        
        # Count total documents in MongoDB
        total_count = await mongo_collection.count_documents({})
        logger.info(f"  Total documents in {collection_name}: {total_count}")
        
        if total_count == 0:
            logger.info(f"  ✓ No documents to process in {collection_name}")
            return (0, 0)
        
        # Get all processed document IDs from ChromaDB
        processed_ids = await get_processed_document_ids(chromadb_collection, collection_name)
        logger.info(f"  Documents already processed: {len(processed_ids)}")
        
        # Get all MongoDB document IDs
        all_mongo_ids = set()
        async for doc in mongo_collection.find({}, {"_id": 1}):
            all_mongo_ids.add(str(doc["_id"]))
        
        # Find unprocessed documents
        unprocessed_ids = all_mongo_ids - processed_ids
        unprocessed_count = len(unprocessed_ids)
        
        if unprocessed_count == 0:
            logger.info(f"  ✓ All documents in {collection_name} are already processed")
            return (0, 0)
        
        logger.info(f"  Unprocessed documents: {unprocessed_count}")
        logger.info(f"  Processing in batches of {batch_size} with {delay_between_batches}s delay...")
        
        # Process in batches
        processed = 0
        failed = 0
        unprocessed_list = list(unprocessed_ids)
        
        for i in range(0, len(unprocessed_list), batch_size):
            batch = unprocessed_list[i:i + batch_size]
            batch_num = (i // batch_size) + 1
            total_batches = (len(unprocessed_list) + batch_size - 1) // batch_size
            
            logger.info(f"  Processing batch {batch_num}/{total_batches} ({len(batch)} documents)...")
            
            # Process each document in the batch
            for doc_id_str in batch:
                try:
                    # Convert string ID back to ObjectId for MongoDB query
                    doc_id = ObjectId(doc_id_str)
                    
                    # Fetch the full document
                    document = await mongo_collection.find_one({"_id": doc_id})
                    
                    if document:
                        success = await process_document(
                            document,
                            collection_name,
                            chromadb_collections
                        )
                        if success:
                            processed += 1
                        else:
                            failed += 1
                    else:
                        logger.warning(f"    Document {doc_id_str} not found in MongoDB")
                        failed += 1
                        
                except Exception as e:
                    logger.error(f"    Error processing document {doc_id_str}: {e}")
                    failed += 1
            
            # Log progress
            logger.info(f"    Batch {batch_num} complete: {processed} processed, {failed} failed so far")
            
            # Delay between batches (except for the last batch)
            if i + batch_size < len(unprocessed_list):
                await asyncio.sleep(delay_between_batches)
        
        logger.info(f"  ✓ Completed processing {collection_name}: {processed} processed, {failed} failed")
        return (processed, failed)
        
    except Exception as e:
        logger.error(f"Error processing unprocessed documents in {collection_name}: {e}")
        return (0, 0)


async def process_all_unprocessed_collections(
    database: Any,
    chromadb_collections: Dict[str, Any],
    collections_to_monitor: List[str],
    batch_size: int = 50,
    delay_between_batches: float = 1.0
):
    """
    Process all unprocessed documents across all monitored collections.
    
    This runs on startup to ensure all existing data is embedded.
    """
    logger.info("=" * 60)
    logger.info("Processing Unprocessed Documents")
    logger.info("=" * 60)
    logger.info("Checking all collections for documents that need embeddings...")
    logger.info("")
    
    total_processed = 0
    total_failed = 0
    
    for collection_name in collections_to_monitor:
        try:
            processed, failed = await process_unprocessed_documents(
                database,
                collection_name,
                chromadb_collections,
                batch_size=batch_size,
                delay_between_batches=delay_between_batches
            )
            total_processed += processed
            total_failed += failed
            logger.info("")  # Empty line between collections
        except Exception as e:
            logger.error(f"Error processing collection {collection_name}: {e}")
            continue
    
    logger.info("=" * 60)
    logger.info(f"Unprocessed Documents Processing Complete")
    logger.info(f"  Total processed: {total_processed}")
    logger.info(f"  Total failed: {total_failed}")
    logger.info("=" * 60)
    logger.info("")


# ============================================================================
# MONGODB CHANGE STREAM MONITOR
# ============================================================================

async def monitor_change_streams(
    database: Any,
    chromadb_collections: Dict[str, Any],
    collections_to_monitor: List[str]
):
    """
    Monitor MongoDB change streams for all specified collections.
    
    Change streams are like notifications - MongoDB tells us when data changes.
    When n8n writes new data (events, traffic, news), this agent immediately creates embeddings.
    
    This runs in an infinite loop, continuously watching for changes.
    """
    logger.info(f"Starting change stream monitoring for {len(collections_to_monitor)} collections...")
    
    try:
        # Create change stream that watches ALL specified collections
        # We filter for 'insert' and 'update' operations (we don't care about deletes)
        pipeline = [
            {"$match": {"operationType": {"$in": ["insert", "update"]}}}
        ]
        
        # Watch all collections at once using database-level change stream
        async with database.watch(pipeline) as stream:
            logger.info("✓ Change stream active - waiting for document changes...")
            logger.info("  When n8n writes data or new orders are created, embeddings will be created automatically")
            
            # Infinite loop - process changes as they arrive
            async for change in stream:
                try:
                    # Get the collection name from the change document
                    collection_name = change.get("ns", {}).get("coll", "")
                    
                    if collection_name not in collections_to_monitor:
                        continue  # Skip collections we're not monitoring
                    
                    # Get the document that changed
                    if change["operationType"] == "insert":
                        document = change.get("fullDocument")
                    elif change["operationType"] == "update":
                        # For updates, we need to fetch the full document
                        document = await database[collection_name].find_one(
                            {"_id": change["documentKey"]["_id"]}
                        )
                    else:
                        continue
                    
                    if document:
                        # Process the document: generate description → create embedding → store in ChromaDB
                        await process_document(document, collection_name, chromadb_collections)
                    else:
                        logger.warning(f"Document not found for change in {collection_name}")
                        
                except Exception as e:
                    # Continue processing even if one document fails
                    logger.error(f"Error processing change stream event: {e}")
                    continue
                    
    except Exception as e:
        logger.error(f"Change stream error: {e}")
        raise


# ============================================================================
# MAIN EXECUTION
# ============================================================================

async def main():
    """
    Main function - sets up connections and starts monitoring.
    
    This agent runs as a standalone process (not part of FastAPI).
    It continuously monitors MongoDB for changes and creates embeddings.
    
    Features:
    - Automatic reconnection on failures
    - Graceful shutdown handling
    - Continuous monitoring of all collections
    """
    logger.info("=" * 60)
    logger.info("Data Ingestion Agent Starting...")
    logger.info("=" * 60)
    logger.info("This agent monitors MongoDB and creates ChromaDB embeddings")
    logger.info("Other agents (Analysis, Pricing, Forecasting, Recommendation) will query these embeddings")
    logger.info("")
    
    mongo_client = None
    max_retries = 5
    retry_delay = 5
    
    while True:
        try:
            # Step 1: Setup ChromaDB (create/get 5 collections)
            logger.info("Step 1: Setting up ChromaDB...")
            try:
                chroma_client, chromadb_collections = setup_chromadb()
                logger.info("✓ ChromaDB ready with 5 collections")
            except Exception as e:
                logger.error(f"Failed to setup ChromaDB: {e}")
                logger.info(f"Retrying in {retry_delay} seconds...")
                await asyncio.sleep(retry_delay)
                continue
            
            # Step 2: Connect to MongoDB
            logger.info("Step 2: Connecting to MongoDB...")
            try:
                mongo_client = AsyncIOMotorClient(settings.mongodb_url)
                database = mongo_client[settings.mongodb_db_name]
                
                # Test connection
                await mongo_client.admin.command('ping')
                logger.info(f"✓ Connected to MongoDB: {settings.mongodb_db_name}")
            except Exception as e:
                logger.error(f"Failed to connect to MongoDB: {e}")
                logger.info(f"Retrying in {retry_delay} seconds...")
                await asyncio.sleep(retry_delay)
                continue
            
            # Step 3: Define collections to monitor
            # These are ALL the collections that might have data we want to embed
            collections_to_monitor = [
                "ride_orders",           # Core ride data
                "events_data",           # From n8n Eventbrite workflow
                "traffic_data",          # From n8n Google Maps workflow
                "news_articles",         # From n8n NewsAPI workflow
                "customers",             # Customer data
                "historical_rides",      # Uploaded historical data
                "competitor_prices"       # Uploaded competitor data
            ]
            
            logger.info(f"Step 3: Monitoring {len(collections_to_monitor)} collections:")
            for coll in collections_to_monitor:
                logger.info(f"  - {coll}")
            logger.info("")
            
            # Step 4: Process any unprocessed existing documents
            # This ensures all existing data gets embedded, not just new inserts
            logger.info("Step 4: Processing unprocessed existing documents...")
            logger.info("  → Checking all collections for documents without embeddings")
            logger.info("  → Processing in batches to minimize performance impact")
            logger.info("")
            
            await process_all_unprocessed_collections(
                database,
                chromadb_collections,
                collections_to_monitor,
                batch_size=50,  # Process 50 documents per batch
                delay_between_batches=1.0  # 1 second delay between batches
            )
            
            # Step 5: Start monitoring change streams for new documents
            logger.info("Step 5: Starting change stream monitoring...")
            logger.info("  → Agent is now running and will process changes in real-time")
            logger.info("  → When n8n writes data or new documents are created, embeddings will be created automatically")
            logger.info("  → Press Ctrl+C to stop")
            logger.info("")
            logger.info("=" * 60)
            
            # This runs forever until interrupted or error
            await monitor_change_streams(database, chromadb_collections, collections_to_monitor)
            
        except KeyboardInterrupt:
            logger.info("")
            logger.info("=" * 60)
            logger.info("Received interrupt signal - shutting down gracefully...")
            logger.info("=" * 60)
            if mongo_client:
                mongo_client.close()
            logger.info("✓ Agent stopped gracefully")
            break
        except Exception as e:
            logger.error(f"Unexpected error in main loop: {e}")
            logger.info(f"Reconnecting in {retry_delay} seconds...")
            if mongo_client:
                try:
                    mongo_client.close()
                except:
                    pass
                mongo_client = None
            await asyncio.sleep(retry_delay)
            continue
        # Cleanup
        mongo_client.close()
        logger.info("✓ Disconnected from MongoDB")
        logger.info("Data Ingestion Agent stopped")


# ============================================================================
# RUN AS STANDALONE SCRIPT
# ============================================================================

if __name__ == "__main__":
    # Run the agent
    # This allows it to be executed directly: python backend/app/agents/data_ingestion.py
    asyncio.run(main())
