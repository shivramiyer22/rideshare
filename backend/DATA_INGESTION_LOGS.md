# Data Ingestion Agent - Log Monitoring Guide

## Overview

The Data Ingestion Agent monitors MongoDB collections and creates ChromaDB embeddings for semantic search. This guide explains how to check logs to ensure it's correctly embedding your uploaded historical data.

## What the Agent Does

1. **Monitors MongoDB Collections**: Watches for new documents in:
   - `historical_rides` (your uploaded historical data)
   - `competitor_prices` (your uploaded competitor data)
   - `ride_orders` (new orders)
   - `events_data`, `traffic_data`, `news_articles` (from n8n)
   - `customers` (customer data)

2. **Creates Embeddings**: For each new document, it:
   - Generates a human-readable text description
   - Creates an embedding using OpenAI API
   - Stores the embedding in ChromaDB with metadata

3. **Enables Semantic Search**: Other agents (Analysis, Pricing, Forecasting, Recommendation) can query ChromaDB to find similar past scenarios.

## Starting the Agent

### Option 1: Foreground (see logs directly)
```bash
cd backend
python app/agents/data_ingestion.py
```

You'll see logs in real-time:
```
============================================================
Data Ingestion Agent Starting...
============================================================
This agent monitors MongoDB and creates ChromaDB embeddings
Other agents (Analysis, Pricing, Forecasting, Recommendation) will query these embeddings

Step 1: Setting up ChromaDB...
✓ ChromaDB ready with 5 collections
Step 2: Connecting to MongoDB...
✓ Connected to MongoDB: rideshare_db
Step 3: Monitoring 7 collections:
  - ride_orders
  - events_data
  - traffic_data
  - news_articles
  - customers
  - historical_rides
  - competitor_prices

Step 4: Starting change stream monitoring...
  → Agent is now running and will process changes in real-time
  → When n8n writes data, embeddings will be created automatically
  → Press Ctrl+C to stop
```

### Option 2: Background (with log file)
```bash
cd backend
nohup python app/agents/data_ingestion.py > /tmp/data_ingestion.log 2>&1 &
```

Then check logs with:
```bash
tail -f /tmp/data_ingestion.log
```

## Checking Logs

### Method 1: Using the Log Checker Script

We've created a helper script to check logs easily:

```bash
# Show last 50 lines
./backend/scripts/check_data_ingestion_logs.sh

# Follow logs in real-time
./backend/scripts/check_data_ingestion_logs.sh -f

# Show last 100 lines
./backend/scripts/check_data_ingestion_logs.sh -n 100

# Filter for historical_rides collection
./backend/scripts/check_data_ingestion_logs.sh -g "historical_rides"

# Follow logs filtered by "embedding"
./backend/scripts/check_data_ingestion_logs.sh -g "embedding" -f
```

### Method 2: Direct Log File Access

If you started the agent with `nohup`:

```bash
# View last 50 lines
tail -n 50 /tmp/data_ingestion.log

# Follow logs in real-time
tail -f /tmp/data_ingestion.log

# Search for specific collection
grep "historical_rides" /tmp/data_ingestion.log

# Search for errors
grep -i "error" /tmp/data_ingestion.log

# Search for successful embeddings
grep "embedding created" /tmp/data_ingestion.log
```

### Method 3: Check if Agent is Running

```bash
# Check if process is running
ps aux | grep data_ingestion.py

# Or use the log checker script
./backend/scripts/check_data_ingestion_logs.sh
```

## What to Look For in Logs

### ✅ Success Indicators

When you upload historical data, you should see logs like:

```
INFO - Processing document from collection: historical_rides
INFO - Generated description: Historical ride on 2024-01-15...
INFO - Created embedding for document
INFO - Stored embedding in ChromaDB collection: historical_data
INFO - ✓ Embedding created successfully for document in historical_rides
```

### ⚠️ Warning Indicators

- **"Empty description"**: Document might not have enough data to create a meaningful description
- **"Failed to create embedding"**: OpenAI API issue (check API key, rate limits)
- **"ChromaDB collection not found"**: ChromaDB setup issue

### ❌ Error Indicators

- **"Failed to connect to MongoDB"**: Check MongoDB connection string
- **"Failed to setup ChromaDB"**: Check ChromaDB installation and permissions
- **"Error processing change stream event"**: Temporary issue, agent will retry

## Verifying Embeddings Were Created

### Method 1: Check ChromaDB Directly

```python
import chromadb
from chromadb.config import Settings

# Connect to ChromaDB
client = chromadb.PersistentClient(
    path="./chroma_db",
    settings=Settings(anonymized_telemetry=False)
)

# Get the historical data collection
collection = client.get_collection("historical_data")

# Count embeddings
count = collection.count()
print(f"Total embeddings in historical_data: {count}")

# Get a few sample embeddings
results = collection.peek(limit=5)
print(f"Sample IDs: {results['ids']}")
```

### Method 2: Query ChromaDB

```python
import chromadb
from chromadb.config import Settings
from openai import OpenAI

# Connect to ChromaDB
client = chromadb.PersistentClient(
    path="./chroma_db",
    settings=Settings(anonymized_telemetry=False)
)

collection = client.get_collection("historical_data")

# Create a query embedding
openai_client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
query_text = "Historical ride with high demand in urban area"
query_embedding = openai_client.embeddings.create(
    model="text-embedding-3-small",
    input=query_text
).data[0].embedding

# Search for similar embeddings
results = collection.query(
    query_embeddings=[query_embedding],
    n_results=5
)

print(f"Found {len(results['ids'][0])} similar documents")
for i, doc_id in enumerate(results['ids'][0]):
    metadata = results['metadatas'][0][i]
    print(f"  {i+1}. MongoDB ID: {metadata['mongodb_id']}")
    print(f"     Description: {metadata['description']}")
```

## Troubleshooting

### Agent Not Processing Uploads

1. **Check if agent is running**:
   ```bash
   ps aux | grep data_ingestion.py
   ```

2. **Check MongoDB connection**:
   - Verify MongoDB is running
   - Check connection string in `.env` file
   - Test connection: `mongosh "your_connection_string"`

3. **Check ChromaDB**:
   - Verify `chroma_db` directory exists and is writable
   - Check disk space

### No Logs After Upload

1. **Verify data was uploaded**:
   ```bash
   # Connect to MongoDB and check
   mongosh "your_connection_string"
   use rideshare_db
   db.historical_rides.countDocuments()
   ```

2. **Check if agent is monitoring the collection**:
   - Look for "Monitoring 7 collections" in logs
   - Verify "historical_rides" is in the list

3. **Check for errors in logs**:
   ```bash
   grep -i error /tmp/data_ingestion.log
   ```

### Embeddings Not Being Created

1. **Check OpenAI API**:
   - Verify `OPENAI_API_KEY` is set in `.env`
   - Check API quota/rate limits
   - Test API: `curl https://api.openai.com/v1/models -H "Authorization: Bearer $OPENAI_API_KEY"`

2. **Check ChromaDB**:
   - Verify directory permissions
   - Check disk space
   - Try recreating ChromaDB collections

## Best Practices

1. **Always run agent in background** for production:
   ```bash
   nohup python app/agents/data_ingestion.py > /tmp/data_ingestion.log 2>&1 &
   ```

2. **Monitor logs regularly** to catch issues early:
   ```bash
   tail -f /tmp/data_ingestion.log
   ```

3. **Set up log rotation** for long-running processes:
   ```bash
   # Use logrotate or similar tool
   ```

4. **Verify embeddings after uploads**:
   - Check logs for success messages
   - Query ChromaDB to confirm embeddings exist
   - Test semantic search to verify quality

## Quick Reference

| Task | Command |
|------|---------|
| Start agent (foreground) | `cd backend && python app/agents/data_ingestion.py` |
| Start agent (background) | `cd backend && nohup python app/agents/data_ingestion.py > /tmp/data_ingestion.log 2>&1 &` |
| Check if running | `ps aux \| grep data_ingestion.py` |
| View logs | `tail -f /tmp/data_ingestion.log` |
| Filter logs | `grep "historical_rides" /tmp/data_ingestion.log` |
| Use log checker | `./backend/scripts/check_data_ingestion_logs.sh -f` |

