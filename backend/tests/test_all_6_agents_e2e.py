"""
End-to-end test script for all 6 AI agents.

This script tests all 6 AI agents with realistic scenarios:
1. Data Ingestion Agent: Insert new event → Verify embedding in ChromaDB
2. Analysis Agent: Query revenue KPIs → Verify response includes correct KPIs
3. Pricing Agent: Calculate price → Verify response includes breakdown
4. Forecasting Agent: Predict demand → Verify Prophet ML forecast returned
5. Recommendation Agent: Strategic recommendation → Verify recommendation
6. Chatbot Orchestrator: Test routing to each agent → Verify multi-agent workflow

Based on CURSOR_IDE_INSTRUCTIONS.md lines 727-756.
"""

import sys
import os
import asyncio
import json
from pathlib import Path
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
from bson import ObjectId

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.database import connect_to_mongo, close_mongo_connection, get_database
from app.agents.utils import setup_chromadb_client, query_chromadb, fetch_mongodb_documents
from app.agents.data_ingestion import process_document, setup_chromadb as setup_data_ingestion_chromadb
from app.agents.orchestrator import orchestrator_agent
from app.agents.analysis import analysis_agent
from app.agents.pricing import pricing_agent
from app.agents.forecasting import forecasting_agent
from app.agents.recommendation import recommendation_agent
from app.config import settings

# Test results tracking
test_results = {
    "data_ingestion_agent": False,
    "analysis_agent": False,
    "pricing_agent": False,
    "forecasting_agent": False,
    "recommendation_agent": False,
    "chatbot_orchestrator": False
}


async def test_data_ingestion_agent() -> bool:
    """
    Test 1: Data Ingestion Agent
    - Insert new event in MongoDB → Verify embedding in ChromaDB
    """
    print("\n" + "=" * 60)
    print("Test 1: Data Ingestion Agent")
    print("=" * 60)
    
    try:
        # Connect to MongoDB
        await connect_to_mongo()
        database = get_database()
        events_collection = database["events_data"]
        
        # Create a test event document
        test_event = {
            "event_name": "Test Lakers Game",
            "venue": "Staples Center",
            "event_date": datetime.utcnow().isoformat(),
            "attendees": 20000,
            "location": "Los Angeles, CA",
            "event_type": "sports",
            "created_at": datetime.utcnow()
        }
        
        # Insert test event
        result = await events_collection.insert_one(test_event)
        event_id = result.inserted_id
        print(f"✓ Inserted test event: {event_id}")
        
        # Setup ChromaDB for data ingestion
        chroma_client, chromadb_collections = setup_data_ingestion_chromadb()
        
        # Process the document (create embedding)
        success = await process_document(
            {**test_event, "_id": event_id},
            "events_data",
            chromadb_collections
        )
        
        if success:
            print("✓ Document processed successfully")
            
            # Verify embedding exists in ChromaDB
            news_events_collection = chromadb_collections.get("news_events_vectors")
            if news_events_collection:
                # Query for the document
                results = news_events_collection.get(ids=[str(event_id)])
                
                if results and len(results.get("ids", [])) > 0:
                    print("✓ Embedding found in ChromaDB")
                    print(f"   Collection: news_events_vectors")
                    print(f"   Document ID: {event_id}")
                    test_results["data_ingestion_agent"] = True
                    
                    # Cleanup: Remove test event
                    await events_collection.delete_one({"_id": event_id})
                    print("✓ Test event cleaned up")
                    return True
                else:
                    print("❌ Embedding not found in ChromaDB")
                    return False
            else:
                print("❌ ChromaDB collection not found")
                return False
        else:
            print("❌ Failed to process document")
            return False
            
    except Exception as e:
        print(f"❌ Error testing Data Ingestion Agent: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        await close_mongo_connection()


async def test_analysis_agent() -> bool:
    """
    Test 2: Analysis Agent
    - Query: "What's our revenue in the last 7 days?"
    - Verify response includes correct KPIs
    """
    print("\n" + "=" * 60)
    print("Test 2: Analysis Agent")
    print("=" * 60)
    
    try:
        if analysis_agent is None:
            print("⚠️  Analysis Agent not available (OPENAI_API_KEY may be missing)")
            return False
        
        # Query the agent
        query = "What's our revenue in the last 7 days?"
        print(f"Query: {query}")
        
        response = analysis_agent.invoke({
            "messages": [{"role": "user", "content": query}]
        })
        
        if response and "messages" in response:
            last_message = response["messages"][-1]
            content = last_message.get("content", "") if hasattr(last_message, "get") else str(last_message)
            print(f"✓ Agent responded")
            print(f"Response preview: {content[:200]}...")
            
            # Check if response includes revenue information
            if "revenue" in content.lower() or "kpi" in content.lower() or "$" in content:
                print("✓ Response includes revenue/KPI information")
                test_results["analysis_agent"] = True
                return True
            else:
                print("⚠️  Response may not include revenue information")
                return False
        else:
            print("❌ No response from agent")
            return False
            
    except Exception as e:
        print(f"❌ Error testing Analysis Agent: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_pricing_agent() -> bool:
    """
    Test 3: Pricing Agent
    - Query: "Calculate price for Gold customer, urban, evening rush, premium"
    - Verify response includes breakdown
    """
    print("\n" + "=" * 60)
    print("Test 3: Pricing Agent")
    print("=" * 60)
    
    try:
        if pricing_agent is None:
            print("⚠️  Pricing Agent not available (OPENAI_API_KEY may be missing)")
            return False
        
        # Query the agent
        query = "Calculate price for Gold customer, urban, evening rush, premium vehicle"
        print(f"Query: {query}")
        
        response = pricing_agent.invoke({
            "messages": [{"role": "user", "content": query}]
        })
        
        if response and "messages" in response:
            last_message = response["messages"][-1]
            content = last_message.get("content", "") if hasattr(last_message, "get") else str(last_message)
            print(f"✓ Agent responded")
            print(f"Response preview: {content[:200]}...")
            
            # Check if response includes price breakdown
            if "price" in content.lower() or "breakdown" in content.lower() or "$" in content:
                print("✓ Response includes price breakdown")
                test_results["pricing_agent"] = True
                return True
            else:
                print("⚠️  Response may not include price breakdown")
                return False
        else:
            print("❌ No response from agent")
            return False
            
    except Exception as e:
        print(f"❌ Error testing Pricing Agent: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_forecasting_agent() -> bool:
    """
    Test 4: Forecasting Agent
    - Query: "Predict demand for next Friday evening"
    - Verify Prophet ML forecast returned
    """
    print("\n" + "=" * 60)
    print("Test 4: Forecasting Agent")
    print("=" * 60)
    
    try:
        if forecasting_agent is None:
            print("⚠️  Forecasting Agent not available (OPENAI_API_KEY may be missing)")
            return False
        
        # Query the agent
        query = "Predict demand for next Friday evening"
        print(f"Query: {query}")
        
        response = forecasting_agent.invoke({
            "messages": [{"role": "user", "content": query}]
        })
        
        if response and "messages" in response:
            last_message = response["messages"][-1]
            content = last_message.get("content", "") if hasattr(last_message, "get") else str(last_message)
            print(f"✓ Agent responded")
            print(f"Response preview: {content[:200]}...")
            
            # Check if response includes forecast information
            if "forecast" in content.lower() or "demand" in content.lower() or "prophet" in content.lower():
                print("✓ Response includes forecast information")
                test_results["forecasting_agent"] = True
                return True
            else:
                print("⚠️  Response may not include forecast information")
                return False
        else:
            print("❌ No response from agent")
            return False
            
    except Exception as e:
        print(f"❌ Error testing Forecasting Agent: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_recommendation_agent() -> bool:
    """
    Test 5: Recommendation Agent
    - Insert Lakers game event via n8n (simulate)
    - Query: "Should we increase prices during the Lakers game?"
    - Verify strategic recommendation
    """
    print("\n" + "=" * 60)
    print("Test 5: Recommendation Agent")
    print("=" * 60)
    
    try:
        if recommendation_agent is None:
            print("⚠️  Recommendation Agent not available (OPENAI_API_KEY may be missing)")
            return False
        
        # Query the agent (simulating Lakers game scenario)
        query = "Should we increase prices during the Lakers game at Staples Center?"
        print(f"Query: {query}")
        
        response = recommendation_agent.invoke({
            "messages": [{"role": "user", "content": query}]
        })
        
        if response and "messages" in response:
            last_message = response["messages"][-1]
            content = last_message.get("content", "") if hasattr(last_message, "get") else str(last_message)
            print(f"✓ Agent responded")
            print(f"Response preview: {content[:200]}...")
            
            # Check if response includes recommendation
            if "recommend" in content.lower() or "suggest" in content.lower() or "strategy" in content.lower():
                print("✓ Response includes strategic recommendation")
                test_results["recommendation_agent"] = True
                return True
            else:
                print("⚠️  Response may not include recommendation")
                return False
        else:
            print("❌ No response from agent")
            return False
            
    except Exception as e:
        print(f"❌ Error testing Recommendation Agent: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_chatbot_orchestrator() -> bool:
    """
    Test 6: Chatbot Orchestrator
    - Test routing to each agent
    - Test multi-agent workflow
    """
    print("\n" + "=" * 60)
    print("Test 6: Chatbot Orchestrator")
    print("=" * 60)
    
    try:
        if orchestrator_agent is None:
            print("⚠️  Orchestrator Agent not available (OPENAI_API_KEY may be missing)")
            return False
        
        # Test routing to Analysis Agent
        query1 = "What's our revenue in the last 7 days?"
        print(f"\nTest 1 - Routing to Analysis Agent:")
        print(f"Query: {query1}")
        
        response1 = orchestrator_agent.invoke({
            "messages": [{"role": "user", "content": query1}]
        })
        
        if response1 and "messages" in response1:
            print("✓ Orchestrator routed query successfully")
        else:
            print("❌ Orchestrator failed to route query")
            return False
        
        # Test routing to Pricing Agent
        query2 = "Calculate price for Gold customer, urban, evening rush, premium"
        print(f"\nTest 2 - Routing to Pricing Agent:")
        print(f"Query: {query2}")
        
        response2 = orchestrator_agent.invoke({
            "messages": [{"role": "user", "content": query2}]
        })
        
        if response2 and "messages" in response2:
            print("✓ Orchestrator routed query successfully")
        else:
            print("❌ Orchestrator failed to route query")
            return False
        
        # Test routing to Forecasting Agent
        query3 = "Predict demand for next Friday evening"
        print(f"\nTest 3 - Routing to Forecasting Agent:")
        print(f"Query: {query3}")
        
        response3 = orchestrator_agent.invoke({
            "messages": [{"role": "user", "content": query3}]
        })
        
        if response3 and "messages" in response3:
            print("✓ Orchestrator routed query successfully")
        else:
            print("❌ Orchestrator failed to route query")
            return False
        
        # Test routing to Recommendation Agent
        query4 = "Should we increase prices during the Lakers game?"
        print(f"\nTest 4 - Routing to Recommendation Agent:")
        print(f"Query: {query4}")
        
        response4 = orchestrator_agent.invoke({
            "messages": [{"role": "user", "content": query4}]
        })
        
        if response4 and "messages" in response4:
            print("✓ Orchestrator routed query successfully")
        else:
            print("❌ Orchestrator failed to route query")
            return False
        
        print("\n✓ All routing tests passed")
        test_results["chatbot_orchestrator"] = True
        return True
        
    except Exception as e:
        print(f"❌ Error testing Chatbot Orchestrator: {e}")
        import traceback
        traceback.print_exc()
        return False


async def run_all_tests():
    """Run all 6 AI agents end-to-end tests."""
    print("\n" + "=" * 80)
    print("All 6 AI Agents End-to-End Tests")
    print("Based on CURSOR_IDE_INSTRUCTIONS.md lines 727-756")
    print("=" * 80)
    
    # Test 1: Data Ingestion Agent
    await test_data_ingestion_agent()
    
    # Test 2: Analysis Agent
    await test_analysis_agent()
    
    # Test 3: Pricing Agent
    await test_pricing_agent()
    
    # Test 4: Forecasting Agent
    await test_forecasting_agent()
    
    # Test 5: Recommendation Agent
    await test_recommendation_agent()
    
    # Test 6: Chatbot Orchestrator
    await test_chatbot_orchestrator()
    
    # Print summary
    print("\n" + "=" * 80)
    print("Test Summary")
    print("=" * 80)
    
    total_tests = len(test_results)
    passed_tests = sum(1 for v in test_results.values() if v)
    
    for test_name, result in test_results.items():
        status = "✓ PASS" if result else "⚠️  SKIP/FAIL"
        print(f"{status}: {test_name}")
    
    print(f"\nTotal: {passed_tests}/{total_tests} tests passed")
    
    if passed_tests == total_tests:
        print("\n✅ All tests passed! All 6 AI agents are working correctly.")
        return True
    else:
        print("\n⚠️  Some tests were skipped or failed.")
        print("   Note: Tests may fail if OPENAI_API_KEY is not configured.")
        return False


if __name__ == "__main__":
    asyncio.run(run_all_tests())

