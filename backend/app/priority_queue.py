"""
Priority Queue Management - Handles P0, P1, P2 priority levels using Redis.
NO Docker - uses native Redis connection.
"""
import json
from enum import Enum
from typing import Dict, Any, Optional, List
from datetime import datetime
from app.redis_client import get_redis
from app.pricing_engine import PricingModel


class Priority(str, Enum):
    """Priority levels."""
    P0 = "P0"  # Critical - highest priority (CONTRACTED orders, FIFO)
    P1 = "P1"  # High priority (STANDARD orders, sorted by revenue_score DESC)
    P2 = "P2"  # Normal priority (CUSTOM orders, sorted by revenue_score DESC)


class PriorityQueue:
    """Priority queue manager for P0, P1, P2 items using Redis."""
    
    # Redis keys for each queue
    P0_KEY = "queue:p0:contracted"  # Redis LIST for FIFO
    P1_KEY = "queue:p1:standard"    # Redis SORTED SET for revenue_score DESC
    P2_KEY = "queue:p2:custom"      # Redis SORTED SET for revenue_score DESC
    
    def __init__(self):
        """Initialize priority queue (Redis connection handled by redis_client)."""
        pass
    
    async def add_order(
        self,
        order_id: str,
        pricing_model: str,
        revenue_score: float,
        order_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Add an order to the appropriate priority queue.
        
        Args:
            order_id: Unique identifier for the order
            pricing_model: CONTRACTED, STANDARD, or CUSTOM
            revenue_score: Revenue score for sorting (used for P1/P2)
            order_data: Order data dictionary
        
        Returns:
            Dict: Order information with priority assigned
        """
        redis = get_redis()
        if not redis:
            raise RuntimeError("Redis connection not available")
        
        # Determine priority based on pricing model
        # Handle both string and enum comparisons
        pricing_model_str = pricing_model.value if isinstance(pricing_model, PricingModel) else str(pricing_model)
        
        if pricing_model_str == PricingModel.CONTRACTED.value:
            priority = Priority.P0
            # P0: Use Redis LIST for FIFO ordering
            order_json = json.dumps({
                "order_id": order_id,
                "pricing_model": pricing_model_str,
                "revenue_score": revenue_score,
                "order_data": order_data,
                "created_at": datetime.utcnow().isoformat()
            })
            await redis.lpush(self.P0_KEY, order_json)
        elif pricing_model_str == PricingModel.STANDARD.value:
            priority = Priority.P1
            # P1: Use Redis SORTED SET sorted by revenue_score DESC
            # Use negative score for DESC order (higher revenue_score = lower negative = first)
            order_json = json.dumps({
                "order_id": order_id,
                "pricing_model": pricing_model_str,
                "revenue_score": revenue_score,
                "order_data": order_data,
                "created_at": datetime.utcnow().isoformat()
            })
            # Negative score for DESC order (highest revenue_score comes first)
            score = -revenue_score
            await redis.zadd(self.P1_KEY, {order_json: score})
        elif pricing_model_str == PricingModel.CUSTOM.value:
            priority = Priority.P2
            # P2: Use Redis SORTED SET sorted by revenue_score DESC
            order_json = json.dumps({
                "order_id": order_id,
                "pricing_model": pricing_model_str,
                "revenue_score": revenue_score,
                "order_data": order_data,
                "created_at": datetime.utcnow().isoformat()
            })
            # Negative score for DESC order
            score = -revenue_score
            await redis.zadd(self.P2_KEY, {order_json: score})
        else:
            raise ValueError(f"Invalid pricing_model: {pricing_model}")
        
        return {
            "order_id": order_id,
            "priority": priority.value,
            "pricing_model": pricing_model_str,
            "revenue_score": revenue_score
        }
    
    async def get_next_p0_order(self) -> Optional[Dict[str, Any]]:
        """
        Get the next CONTRACTED order from P0 queue (FIFO).
        
        Returns:
            Optional[Dict]: Order data or None if queue is empty
        """
        redis = get_redis()
        if not redis:
            raise RuntimeError("Redis connection not available")
        
        # P0: RPOP from LIST (FIFO - first in, first out)
        order_json = await redis.rpop(self.P0_KEY)
        if not order_json:
            return None
        
        order = json.loads(order_json)
        order["processed_at"] = datetime.utcnow().isoformat()
        return order
    
    async def get_next_p1_order(self) -> Optional[Dict[str, Any]]:
        """
        Get the next STANDARD order from P1 queue (highest revenue_score).
        
        Returns:
            Optional[Dict]: Order data or None if queue is empty
        """
        redis = get_redis()
        if not redis:
            raise RuntimeError("Redis connection not available")
        
        # P1: ZREVRANGE from SORTED SET (highest revenue_score first)
        # Get the first element (index 0) with highest score
        results = await redis.zrevrange(self.P1_KEY, 0, 0, withscores=True)
        if not results:
            return None
        
        order_json, score = results[0]
        order = json.loads(order_json)
        order["processed_at"] = datetime.utcnow().isoformat()
        
        # Remove from queue
        await redis.zrem(self.P1_KEY, order_json)
        
        return order
    
    async def get_next_p2_order(self) -> Optional[Dict[str, Any]]:
        """
        Get the next CUSTOM order from P2 queue (highest revenue_score).
        
        Returns:
            Optional[Dict]: Order data or None if queue is empty
        """
        redis = get_redis()
        if not redis:
            raise RuntimeError("Redis connection not available")
        
        # P2: ZREVRANGE from SORTED SET (highest revenue_score first)
        results = await redis.zrevrange(self.P2_KEY, 0, 0, withscores=True)
        if not results:
            return None
        
        order_json, score = results[0]
        order = json.loads(order_json)
        order["processed_at"] = datetime.utcnow().isoformat()
        
        # Remove from queue
        await redis.zrem(self.P2_KEY, order_json)
        
        return order
    
    async def get_p0_orders(self, limit: int = 100) -> List[Dict[str, Any]]:
        """
        Get all CONTRACTED orders from P0 queue (FIFO order).
        
        Args:
            limit: Maximum number of orders to return (default: 100)
        
        Returns:
            List[Dict]: List of order dictionaries in FIFO order
        """
        redis = get_redis()
        if not redis:
            raise RuntimeError("Redis connection not available")
        
        # P0: Get all items from LIST (FIFO order - oldest first)
        # LRANGE gets items from left to right (oldest to newest)
        order_jsons = await redis.lrange(self.P0_KEY, 0, limit - 1)
        
        orders = []
        for order_json in order_jsons:
            try:
                order = json.loads(order_json)
                orders.append(order)
            except json.JSONDecodeError:
                continue
        
        return orders
    
    async def get_p1_orders(self, limit: int = 100) -> List[Dict[str, Any]]:
        """
        Get all STANDARD orders from P1 queue (sorted by revenue_score DESC).
        
        Args:
            limit: Maximum number of orders to return (default: 100)
        
        Returns:
            List[Dict]: List of order dictionaries sorted by revenue_score DESC
        """
        redis = get_redis()
        if not redis:
            raise RuntimeError("Redis connection not available")
        
        # P1: Get all items from SORTED SET (sorted by revenue_score DESC)
        # ZREVRANGE gets items with highest score first
        results = await redis.zrevrange(self.P1_KEY, 0, limit - 1, withscores=True)
        
        orders = []
        for order_json, score in results:
            try:
                order = json.loads(order_json)
                orders.append(order)
            except json.JSONDecodeError:
                continue
        
        return orders
    
    async def get_p2_orders(self, limit: int = 100) -> List[Dict[str, Any]]:
        """
        Get all CUSTOM orders from P2 queue (sorted by revenue_score DESC).
        
        Args:
            limit: Maximum number of orders to return (default: 100)
        
        Returns:
            List[Dict]: List of order dictionaries sorted by revenue_score DESC
        """
        redis = get_redis()
        if not redis:
            raise RuntimeError("Redis connection not available")
        
        # P2: Get all items from SORTED SET (sorted by revenue_score DESC)
        results = await redis.zrevrange(self.P2_KEY, 0, limit - 1, withscores=True)
        
        orders = []
        for order_json, score in results:
            try:
                order = json.loads(order_json)
                orders.append(order)
            except json.JSONDecodeError:
                continue
        
        return orders
    
    async def get_queue_status(self) -> Dict[str, int]:
        """
        Get status of the queue by priority level.
        
        Returns:
            Dict: Count of items by priority
        """
        redis = get_redis()
        if not redis:
            raise RuntimeError("Redis connection not available")
        
        # Get counts from Redis
        p0_count = await redis.llen(self.P0_KEY)
        p1_count = await redis.zcard(self.P1_KEY)
        p2_count = await redis.zcard(self.P2_KEY)
        
        return {
            Priority.P0.value: p0_count,
            Priority.P1.value: p1_count,
            Priority.P2.value: p2_count
        }
    
    async def clear_queue(self, priority: Priority) -> bool:
        """
        Clear a specific priority queue.
        
        Args:
            priority: Priority level to clear
        
        Returns:
            bool: True if cleared successfully
        """
        redis = get_redis()
        if not redis:
            raise RuntimeError("Redis connection not available")
        
        if priority == Priority.P0:
            await redis.delete(self.P0_KEY)
        elif priority == Priority.P1:
            await redis.delete(self.P1_KEY)
        elif priority == Priority.P2:
            await redis.delete(self.P2_KEY)
        else:
            return False
        
        return True


# Global priority queue instance
priority_queue = PriorityQueue()

