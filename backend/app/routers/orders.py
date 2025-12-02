"""
Routes and endpoints related to orders and priority queues.
"""
from fastapi import APIRouter, HTTPException
from typing import List, Dict, Any
from datetime import datetime
import uuid
from app.models.schemas import OrderCreate, OrderResponse, OrderStatus
from app.priority_queue import PriorityQueue
from app.database import get_database
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/orders", tags=["orders"])

# Initialize priority queue
priority_queue = PriorityQueue()


@router.get("/", response_model=List[OrderResponse])
async def get_orders():
    """Get all orders from MongoDB."""
    try:
        database = get_database()
        if database is None:
            raise HTTPException(status_code=500, detail="Database connection not available")
        
        collection = database["orders"]
        cursor = collection.find({}).sort("created_at", -1).limit(100)
        orders = await cursor.to_list(length=100)
        
        # Convert MongoDB documents to OrderResponse format
        result = []
        for order in orders:
            result.append(OrderResponse(
                id=order.get("id", str(order.get("_id", ""))),
                user_id=order.get("user_id", ""),
                pickup_location=order.get("pickup_location", {}),
                dropoff_location=order.get("dropoff_location", {}),
                status=OrderStatus(order.get("status", "PENDING")),
                pricing_tier=order.get("pricing_tier", "STANDARD"),
                priority=order.get("priority", "P2"),
                price=order.get("price"),
                created_at=order.get("created_at", datetime.utcnow()),
                updated_at=order.get("updated_at", datetime.utcnow())
            ))
        return result
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching orders: {e}")
        raise HTTPException(status_code=500, detail=f"Error fetching orders: {str(e)}")


@router.get("/{order_id}", response_model=OrderResponse)
async def get_order(order_id: str):
    """Get a specific order by ID."""
    try:
        database = get_database()
        if database is None:
            raise HTTPException(status_code=500, detail="Database connection not available")
        
        collection = database["orders"]
        order = await collection.find_one({"id": order_id})
        
        if not order:
            raise HTTPException(status_code=404, detail="Order not found")
        
        return OrderResponse(
            id=order.get("id", str(order.get("_id", ""))),
            user_id=order.get("user_id", ""),
            pickup_location=order.get("pickup_location", {}),
            dropoff_location=order.get("dropoff_location", {}),
            status=OrderStatus(order.get("status", "PENDING")),
            pricing_tier=order.get("pricing_tier", "STANDARD"),
            priority=order.get("priority", "P2"),
            price=order.get("price"),
            created_at=order.get("created_at", datetime.utcnow()),
            updated_at=order.get("updated_at", datetime.utcnow())
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching order {order_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Error fetching order: {str(e)}")


@router.post("/", response_model=OrderResponse)
async def create_order(order: OrderCreate):
    """
    Create a new order.
    
    This endpoint:
    1. Creates a unique order ID
    2. Saves the order to MongoDB
    3. Adds the order to the appropriate priority queue (P0/P1/P2)
    4. Returns the created order
    """
    try:
        database = get_database()
        if database is None:
            raise HTTPException(status_code=500, detail="Database connection not available")
        
        # Generate unique order ID
        order_id = f"ORD-{uuid.uuid4().hex[:8].upper()}"
        now = datetime.utcnow()
        
        # Determine priority based on pricing_tier
        # CONTRACTED -> P0 (highest priority, FIFO)
        # STANDARD -> P1 (high priority, sorted by revenue)
        # CUSTOM -> P2 (normal priority, sorted by revenue)
        pricing_to_priority = {
            "CONTRACTED": "P0",
            "STANDARD": "P1", 
            "CUSTOM": "P2"
        }
        priority = pricing_to_priority.get(order.pricing_tier.upper(), order.priority)
        
        # Create order document
        order_doc = {
            "id": order_id,
            "user_id": order.user_id,
            "pickup_location": order.pickup_location,
            "dropoff_location": order.dropoff_location,
            "status": OrderStatus.PENDING.value,
            "pricing_tier": order.pricing_tier.upper(),
            "priority": priority,
            "price": None,  # Price calculated later by pricing engine
            "created_at": now,
            "updated_at": now
        }
        
        # Save to MongoDB
        collection = database["orders"]
        await collection.insert_one(order_doc)
        logger.info(f"Created order {order_id} for user {order.user_id}")
        
        # Add to priority queue (Redis)
        try:
            # Calculate a simple revenue score based on pricing tier
            revenue_scores = {"CONTRACTED": 100, "STANDARD": 75, "CUSTOM": 50}
            revenue_score = revenue_scores.get(order.pricing_tier.upper(), 50)
            
            await priority_queue.add_order(
                order_id=order_id,
                pricing_model=order.pricing_tier.upper(),
                revenue_score=revenue_score,
                order_data=order_doc
            )
            logger.info(f"Added order {order_id} to priority queue {priority}")
        except Exception as queue_error:
            # Log but don't fail - order is already in MongoDB
            logger.warning(f"Could not add order to priority queue: {queue_error}")
        
        # Return created order
        return OrderResponse(
            id=order_id,
            user_id=order.user_id,
            pickup_location=order.pickup_location,
            dropoff_location=order.dropoff_location,
            status=OrderStatus.PENDING,
            pricing_tier=order.pricing_tier.upper(),
            priority=priority,
            price=None,
            created_at=now,
            updated_at=now
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating order: {e}")
        raise HTTPException(status_code=500, detail=f"Error creating order: {str(e)}")


@router.get("/queue/priority")
async def get_priority_queue() -> Dict[str, Any]:
    """
    Get all orders from P0, P1, P2 priority queues.
    
    Returns:
        Dictionary with:
            - P0: List of CONTRACTED orders (FIFO order)
            - P1: List of STANDARD orders (sorted by revenue_score DESC)
            - P2: List of CUSTOM orders (sorted by revenue_score DESC)
            - status: Dictionary with counts for each queue
    """
    try:
        # Fetch orders from all queues
        p0_orders = await priority_queue.get_p0_orders(limit=100)
        p1_orders = await priority_queue.get_p1_orders(limit=100)
        p2_orders = await priority_queue.get_p2_orders(limit=100)
        
        # Get queue status (counts)
        status = await priority_queue.get_queue_status()
        
        return {
            "P0": p0_orders,
            "P1": p1_orders,
            "P2": p2_orders,
            "status": status
        }
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error fetching priority queue: {str(e)}"
        )


