"""
Routes and endpoints related to orders and priority queues.
"""
from fastapi import APIRouter, HTTPException
from typing import List, Dict, Any
from datetime import datetime
import uuid
from app.models.schemas import (
    OrderCreate, OrderResponse, OrderStatus,
    OrderEstimateRequest, OrderEstimateResponse,
    SegmentData, HistoricalBaseline, ForecastPrediction, PriceBreakdown
)
from app.priority_queue import PriorityQueue
from app.database import get_database
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/orders", tags=["orders"])

# Initialize priority queue
priority_queue = PriorityQueue()


@router.post("/estimate", response_model=OrderEstimateResponse)
async def estimate_order_price(request: OrderEstimateRequest):
    """
    Estimate price for order based on segment dimensions.
    
    This endpoint provides comprehensive price estimation WITHOUT creating an order.
    It combines:
    1. Historical baseline (avg price, distance, duration from past rides)
    2. Forecast prediction (30-day price/demand forecast)
    3. Estimated price (segment average OR PricingEngine calculation if trip details provided)
    4. Price breakdown (if distance/duration provided)
    5. Natural language explanation and assumptions
    
    This is a read-only endpoint - no order is created.
    Frontend can call this multiple times as user changes inputs.
    Perfect for "price preview" functionality before order submission.
    
    Args:
        request: OrderEstimateRequest with segment dimensions and optional trip details
    
    Returns:
        OrderEstimateResponse with all computed pricing data
        
    Example Request:
        {
          "location_category": "Urban",
          "loyalty_tier": "Gold",
          "vehicle_type": "Premium",
          "pricing_model": "STANDARD",
          "distance": 10.5,
          "duration": 25.0
        }
    """
    try:
        from app.agents.segment_analysis import calculate_segment_estimate
        
        logger.info(f"Estimating price for segment: {request.location_category}/{request.loyalty_tier}/{request.vehicle_type}/{request.pricing_model}")
        
        # Build segment dimensions dict
        segment_dimensions = {
            "location_category": request.location_category,
            "loyalty_tier": request.loyalty_tier,
            "vehicle_type": request.vehicle_type,
            "pricing_model": request.pricing_model
        }
        
        # Build trip details dict if provided
        trip_details = None
        if request.distance is not None and request.duration is not None:
            trip_details = {
                "distance": request.distance,
                "duration": request.duration
            }
            logger.info(f"Trip details provided: {request.distance}mi, {request.duration}min")
        
        # Calculate estimate using segment analysis
        estimate = await calculate_segment_estimate(segment_dimensions, trip_details)
        
        # Build response
        return OrderEstimateResponse(
            segment=SegmentData(**segment_dimensions),
            historical_baseline=HistoricalBaseline(**estimate["historical_baseline"]),
            forecast_prediction=ForecastPrediction(**estimate["forecast_prediction"]),
            estimated_price=estimate["estimated_price"],
            price_breakdown=PriceBreakdown(**estimate["price_breakdown"]) if estimate.get("price_breakdown") else None,
            explanation=estimate["explanation"],
            assumptions=estimate["assumptions"]
        )
    
    except Exception as e:
        logger.error(f"Error estimating order price: {e}")
        raise HTTPException(status_code=500, detail=f"Error estimating price: {str(e)}")


@router.get("/", response_model=List[OrderResponse])
async def get_orders():
    """Get all orders from MongoDB."""
    try:
        database = get_database()
        if database is None:
            raise HTTPException(status_code=500, detail="Database connection not available")
        
        # Use 'orders' collection (actual collection name in MongoDB)
        collection = database["orders"]
        cursor = collection.find({}).sort("created_at", -1).limit(100)
        orders = await cursor.to_list(length=100)
        
        # Convert MongoDB documents to OrderResponse format
        result = []
        for order in orders:
            # Parse datetime strings if they're strings
            created_at = order.get("created_at")
            if isinstance(created_at, str):
                try:
                    from dateutil import parser
                    created_at = parser.parse(created_at)
                except:
                    created_at = datetime.utcnow()
            elif not isinstance(created_at, datetime):
                created_at = datetime.utcnow()
            
            updated_at = order.get("updated_at")
            if isinstance(updated_at, str):
                try:
                    from dateutil import parser
                    updated_at = parser.parse(updated_at)
                except:
                    updated_at = datetime.utcnow()
            elif not isinstance(updated_at, datetime):
                updated_at = datetime.utcnow()
            
            result.append(OrderResponse(
                id=order.get("id", str(order.get("_id", ""))),
                user_id=order.get("user_id", ""),
                pickup_location=order.get("pickup_location", {}),
                dropoff_location=order.get("dropoff_location", {}),
                status=OrderStatus(order.get("status", "PENDING")),
                # Segment dimensions
                location_category=order.get("location_category", "Urban"),
                loyalty_tier=order.get("loyalty_tier", "Regular"),
                vehicle_type=order.get("vehicle_type", "Economy"),
                pricing_model=order.get("pricing_model", "STANDARD"),
                # Computed fields with NEW data model
                segment_avg_fcs_unit_price=order.get("segment_avg_fcs_unit_price"),
                segment_avg_fcs_ride_duration=order.get("segment_avg_fcs_ride_duration"),
                segment_avg_riders_per_order=order.get("segment_avg_riders_per_order"),
                segment_avg_drivers_per_order=order.get("segment_avg_drivers_per_order"),
                segment_demand_profile=order.get("segment_demand_profile"),
                estimated_price=order.get("estimated_price", 0.0),
                price_breakdown=order.get("price_breakdown"),
                pricing_explanation=order.get("pricing_explanation"),
                # Priority
                priority=order.get("priority", "P2"),
                created_at=created_at,
                updated_at=updated_at
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
        
        # Use 'orders' collection (actual collection name in MongoDB)
        collection = database["orders"]
        order = await collection.find_one({"id": order_id})
        
        if not order:
            raise HTTPException(status_code=404, detail="Order not found")
        
        # Parse datetime strings if they're strings
        created_at = order.get("created_at")
        if isinstance(created_at, str):
            try:
                from dateutil import parser
                created_at = parser.parse(created_at)
            except:
                created_at = datetime.utcnow()
        elif not isinstance(created_at, datetime):
            created_at = datetime.utcnow()
        
        updated_at = order.get("updated_at")
        if isinstance(updated_at, str):
            try:
                from dateutil import parser
                updated_at = parser.parse(updated_at)
            except:
                updated_at = datetime.utcnow()
        elif not isinstance(updated_at, datetime):
            updated_at = datetime.utcnow()
        
        return OrderResponse(
            id=order.get("id", str(order.get("_id", ""))),
            user_id=order.get("user_id", ""),
            pickup_location=order.get("pickup_location", {}),
            dropoff_location=order.get("dropoff_location", {}),
            status=OrderStatus(order.get("status", "PENDING")),
            # Segment dimensions
            location_category=order.get("location_category", "Urban"),
            loyalty_tier=order.get("loyalty_tier", "Regular"),
            vehicle_type=order.get("vehicle_type", "Economy"),
            pricing_model=order.get("pricing_model", "STANDARD"),
            # Computed fields with NEW data model
            segment_avg_fcs_unit_price=order.get("segment_avg_fcs_unit_price"),
            segment_avg_fcs_ride_duration=order.get("segment_avg_fcs_ride_duration"),
            segment_avg_riders_per_order=order.get("segment_avg_riders_per_order"),
            segment_avg_drivers_per_order=order.get("segment_avg_drivers_per_order"),
            segment_demand_profile=order.get("segment_demand_profile"),
            estimated_price=order.get("estimated_price", 0.0),
            price_breakdown=order.get("price_breakdown"),
            pricing_explanation=order.get("pricing_explanation"),
            # Priority
            priority=order.get("priority", "P2"),
            created_at=created_at,
            updated_at=updated_at
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching order {order_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Error fetching order: {str(e)}")


@router.post("/", response_model=OrderResponse)
async def create_order(order: OrderCreate):
    """
    Create a new order with computed pricing data.
    
    Enhanced to include:
    1. Segment analysis (avg price, distance from historical data)
    2. Price estimation (PricingEngine calculation if distance/duration provided)
    3. All computed fields stored in MongoDB for analytics
    
    Steps:
    1. Calculate segment estimates using segment_analysis helper
    2. Create order with computed pricing fields
    3. Save to MongoDB (ride_orders collection)
    4. Add to priority queue
    5. Return created order
    
    Args:
        order: OrderCreate with segment dimensions and optional trip details
    
    Returns:
        OrderResponse with all computed pricing fields populated
    """
    try:
        from app.agents.segment_analysis import calculate_segment_estimate
        
        database = get_database()
        if database is None:
            raise HTTPException(status_code=500, detail="Database connection not available")
        
        logger.info(f"Creating order for user {order.user_id} with segment: {order.location_category}/{order.loyalty_tier}/{order.vehicle_type}/{order.pricing_model}")
        
        # Build segment dimensions
        segment_dimensions = {
            "location_category": order.location_category,
            "loyalty_tier": order.loyalty_tier,
            "vehicle_type": order.vehicle_type,
            "pricing_model": order.pricing_model
        }
        
        # Build trip details if provided
        trip_details = None
        if order.distance and order.duration:
            trip_details = {
                "distance": order.distance,
                "duration": order.duration
            }
            logger.info(f"Trip details: {order.distance}mi, {order.duration}min")
        
        # Calculate estimates using segment analysis
        estimate = await calculate_segment_estimate(segment_dimensions, trip_details)
        
        # Generate unique order ID
        order_id = str(uuid.uuid4())
        now = datetime.utcnow()
        
        # Determine priority based on pricing_model
        # CONTRACTED -> P0 (highest priority, FIFO)
        # STANDARD -> P1 (high priority, sorted by revenue)
        # CUSTOM -> P2 (normal priority, sorted by revenue)
        pricing_to_priority = {
            "CONTRACTED": "P0",
            "STANDARD": "P1",
            "CUSTOM": "P2"
        }
        priority = pricing_to_priority.get(order.pricing_model.upper(), order.priority)
        
        # Build order document with computed fields
        order_doc = {
            "id": order_id,
            "user_id": order.user_id,
            "pickup_location": order.pickup_location,
            "dropoff_location": order.dropoff_location,
            "status": OrderStatus.PENDING.value,
            
            # Segment dimensions
            "location_category": order.location_category,
            "loyalty_tier": order.loyalty_tier,
            "vehicle_type": order.vehicle_type,
            "pricing_model": order.pricing_model,
            
            # Computed pricing fields with NEW data model
            "segment_avg_fcs_unit_price": estimate["historical_baseline"].get("segment_avg_fcs_unit_price", 0.0),
            "segment_avg_fcs_ride_duration": estimate["historical_baseline"].get("segment_avg_fcs_ride_duration", 0.0),
            "segment_avg_riders_per_order": estimate["historical_baseline"].get("segment_avg_riders_per_order", 0.0),
            "segment_avg_drivers_per_order": estimate["historical_baseline"].get("segment_avg_drivers_per_order", 0.0),
            "segment_demand_profile": estimate["historical_baseline"].get("segment_demand_profile", "MEDIUM"),
            "estimated_price": estimate["estimated_price"],
            "price_breakdown": estimate.get("price_breakdown"),
            "pricing_explanation": estimate["explanation"],
            
            # Trip details
            "distance": order.distance,
            "duration": order.duration,
            
            # Priority
            "priority": priority,
            
            "created_at": now,
            "updated_at": now
        }
        
        # Save to MongoDB (orders collection - the actual collection name)
        collection = database["orders"]
        await collection.insert_one(order_doc)
        logger.info(f"Created order {order_id} with estimated price ${estimate['estimated_price']:.2f}")
        
        # Add to priority queue (Redis)
        try:
            # Use estimated price as revenue score
            revenue_score = estimate["estimated_price"]
            
            await priority_queue.add_order(
                order_id=order_id,
                pricing_model=order.pricing_model.upper(),
                revenue_score=revenue_score,
                order_data=order_doc
            )
            logger.info(f"Added order {order_id} to priority queue {priority} with revenue_score=${revenue_score:.2f}")
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
            # Segment dimensions
            location_category=order.location_category,
            loyalty_tier=order.loyalty_tier,
            vehicle_type=order.vehicle_type,
            pricing_model=order.pricing_model,
            # Computed fields with NEW data model
            segment_avg_fcs_unit_price=estimate["historical_baseline"].get("segment_avg_fcs_unit_price", 0.0),
            segment_avg_fcs_ride_duration=estimate["historical_baseline"].get("segment_avg_fcs_ride_duration", 0.0),
            segment_avg_riders_per_order=estimate["historical_baseline"].get("segment_avg_riders_per_order", 0.0),
            segment_avg_drivers_per_order=estimate["historical_baseline"].get("segment_avg_drivers_per_order", 0.0),
            segment_demand_profile=estimate["historical_baseline"].get("segment_demand_profile", "MEDIUM"),
            estimated_price=estimate["estimated_price"],
            price_breakdown=estimate.get("price_breakdown"),
            pricing_explanation=estimate["explanation"],
            # Priority
            priority=priority,
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


