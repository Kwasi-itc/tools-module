from sqlalchemy.orm import Session
from sqlalchemy import func, and_
from datetime import datetime, timedelta
from uuid import UUID
from typing import Dict, Any
from app.database.models import ToolRateLimit, ToolExecution, RateLimitScope


class RateLimitService:
    """Service for rate limiting"""
    
    @staticmethod
    def check_rate_limit(
        db: Session,
        tool_id: UUID,
        agent_id: str,
        role_id: UUID
    ) -> Dict[str, Any]:
        """
        Check if execution is allowed based on rate limits.
        
        Returns:
            Dict with 'allowed' (bool) and optional 'message'
        """
        # Get all rate limits for this tool
        rate_limits = db.query(ToolRateLimit).filter(
            ToolRateLimit.tool_id == tool_id
        ).all()
        
        if not rate_limits:
            # No rate limits configured, allow execution
            return {"allowed": True}
        
        # Check each rate limit
        for rate_limit in rate_limits:
            if rate_limit.scope == RateLimitScope.GLOBAL:
                # Check global limit
                window_start = datetime.utcnow() - timedelta(
                    seconds=rate_limit.time_window_seconds
                )
                count = db.query(ToolExecution).filter(
                    ToolExecution.tool_id == tool_id,
                    ToolExecution.created_at >= window_start,
                    ToolExecution.status.in_(["success", "failed"])  # Count completed executions
                ).count()
                
                if count >= rate_limit.max_requests:
                    return {
                        "allowed": False,
                        "message": f"Global rate limit exceeded: {rate_limit.max_requests} requests per {rate_limit.time_window_seconds} seconds"
                    }
            
            elif rate_limit.scope == RateLimitScope.AGENT:
                # Check per-agent limit
                window_start = datetime.utcnow() - timedelta(
                    seconds=rate_limit.time_window_seconds
                )
                count = db.query(ToolExecution).filter(
                    ToolExecution.tool_id == tool_id,
                    ToolExecution.agent_id == agent_id,
                    ToolExecution.created_at >= window_start,
                    ToolExecution.status.in_(["success", "failed"])
                ).count()
                
                if count >= rate_limit.max_requests:
                    return {
                        "allowed": False,
                        "message": f"Agent rate limit exceeded: {rate_limit.max_requests} requests per {rate_limit.time_window_seconds} seconds"
                    }
            
            elif rate_limit.scope == RateLimitScope.USER:
                # Check per-role limit (using role_id as user identifier)
                window_start = datetime.utcnow() - timedelta(
                    seconds=rate_limit.time_window_seconds
                )
                count = db.query(ToolExecution).filter(
                    ToolExecution.tool_id == tool_id,
                    ToolExecution.role_id == role_id,
                    ToolExecution.created_at >= window_start,
                    ToolExecution.status.in_(["success", "failed"])
                ).count()
                
                if count >= rate_limit.max_requests:
                    return {
                        "allowed": False,
                        "message": f"Role rate limit exceeded: {rate_limit.max_requests} requests per {rate_limit.time_window_seconds} seconds"
                    }
        
        return {"allowed": True}
    
    @staticmethod
    def record_usage(
        db: Session,
        tool_id: UUID,
        agent_id: str,
        role_id: UUID
    ) -> None:
        """
        Record tool usage for rate limiting.
        This is called after successful execution.
        """
        # Usage is already recorded in ToolExecution table
        # This method can be extended for additional tracking if needed
        pass

