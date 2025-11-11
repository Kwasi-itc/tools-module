from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import Optional
from uuid import UUID

from app.database.database import get_db
from app.schemas.analytics import (
    ToolStatsResponse, ExecutionStatsResponse, ToolUsageStatsResponse,
    RateLimitStatusResponse, AgentStatsResponse, RoleStatsResponse,
    TopToolsResponse, TopToolResponse
)
from app.services.analytics_service import AnalyticsService

router = APIRouter(prefix="/analytics", tags=["analytics-monitoring"])


@router.get("/stats/executions", response_model=ExecutionStatsResponse)
async def get_execution_stats(
    db: Session = Depends(get_db)
):
    """Get overall execution statistics across all tools"""
    return AnalyticsService.get_execution_stats(db)


@router.get("/stats/tool/{tool_id}", response_model=ToolStatsResponse)
async def get_tool_stats(
    tool_id: UUID,
    db: Session = Depends(get_db)
):
    """Get statistics for a specific tool"""
    stats = AnalyticsService.get_tool_stats(db, tool_id)
    if not stats:
        raise HTTPException(status_code=404, detail="Tool not found")
    
    return stats


@router.get("/stats/agent/{agent_id}", response_model=AgentStatsResponse)
async def get_agent_stats(
    agent_id: str,
    db: Session = Depends(get_db)
):
    """Get statistics for a specific agent"""
    stats = AnalyticsService.get_agent_stats(db, agent_id)
    if not stats:
        raise HTTPException(
            status_code=404,
            detail=f"No execution history found for agent '{agent_id}'"
        )
    
    return stats


@router.get("/stats/role/{role_id}", response_model=RoleStatsResponse)
async def get_role_stats(
    role_id: UUID,
    db: Session = Depends(get_db)
):
    """Get statistics for a specific role"""
    stats = AnalyticsService.get_role_stats(db, role_id)
    if not stats:
        raise HTTPException(
            status_code=404,
            detail="Role not found or has no execution history"
        )
    
    return stats


@router.get("/usage/tool/{tool_id}", response_model=ToolUsageStatsResponse)
async def get_tool_usage_stats(
    tool_id: UUID,
    period: str = Query("day", description="Time period: hour, day, week, month"),
    days: int = Query(7, ge=1, le=365, description="Number of days to analyze"),
    db: Session = Depends(get_db)
):
    """Get tool usage statistics over time"""
    if period not in ["hour", "day", "week", "month"]:
        raise HTTPException(
            status_code=400,
            detail="Period must be one of: hour, day, week, month"
        )
    
    stats = AnalyticsService.get_tool_usage_stats(db, tool_id, period, days)
    if not stats:
        raise HTTPException(status_code=404, detail="Tool not found")
    
    return stats


@router.get("/rate-limits/tool/{tool_id}", response_model=RateLimitStatusResponse)
async def get_rate_limit_status(
    tool_id: UUID,
    agent_id: Optional[str] = Query(None, description="Agent ID for agent-scoped limits"),
    role_id: Optional[UUID] = Query(None, description="Role ID for role-scoped limits"),
    db: Session = Depends(get_db)
):
    """Get rate limit status for a tool"""
    status = AnalyticsService.get_rate_limit_status(db, tool_id, agent_id, role_id)
    if not status:
        raise HTTPException(status_code=404, detail="Tool not found")
    
    return status


@router.get("/top-tools", response_model=TopToolsResponse)
async def get_top_tools(
    limit: int = Query(10, ge=1, le=100, description="Number of top tools to return"),
    days: Optional[int] = Query(None, ge=1, le=365, description="Filter by last N days"),
    db: Session = Depends(get_db)
):
    """Get top tools by execution count"""
    tools = AnalyticsService.get_top_tools(db, limit, days)
    
    return TopToolsResponse(
        tools=tools,
        period=f"last {days} days" if days else "all time",
        limit=limit
    )

