"""
Routes and endpoints related to orders and priority queues.
"""
from fastapi import APIRouter, HTTPException
from typing import List, Dict, Any
from app.models.schemas import OrderCreate, OrderResponse
from app.priority_queue import PriorityQueue

router = APIRouter(prefix="/orders", tags=["orders"])

# Initialize priority queue
priority_queue = PriorityQueue()


@router.get("/", response_model=List[OrderResponse])
async def get_orders():
    """Get all orders."""
    # TODO: Implement order retrieval
    return []


@router.get("/{order_id}", response_model=OrderResponse)
async def get_order(order_id: str):
    """Get a specific order by ID."""
    # TODO: Implement order retrieval by ID
    raise HTTPException(status_code=404, detail="Order not found")


@router.post("/", response_model=OrderResponse)
async def create_order(order: OrderCreate):
    """Create a new order."""
    # TODO: Implement order creation
    raise HTTPException(status_code=501, detail="Not implemented")


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


