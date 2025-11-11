from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime
from uuid import UUID
from app.database.models import ExecutionStatus


class ToolStatsResponse(BaseModel):
    """Statistics for a specific tool"""
    tool_id: UUID
    tool_name: str
    total_executions: int
    successful_executions: int
    failed_executions: int
    success_rate: float = Field(..., description="Success rate as percentage (0-100)")
    average_execution_time_ms: Optional[float] = None
    total_cost: Optional[float] = None
    last_execution_at: Optional[datetime] = None


class ExecutionStatsResponse(BaseModel):
    """Overall execution statistics"""
    total_executions: int
    successful_executions: int
    failed_executions: int
    pending_executions: int
    running_executions: int
    success_rate: float
    average_execution_time_ms: Optional[float] = None
    total_cost: Optional[float] = None


class TimeSeriesDataPoint(BaseModel):
    """Data point for time series"""
    timestamp: datetime
    value: float
    label: Optional[str] = None


class ToolUsageStatsResponse(BaseModel):
    """Tool usage statistics over time"""
    tool_id: UUID
    tool_name: str
    time_series: List[TimeSeriesDataPoint]
    period: str = Field(..., description="Time period: 'hour', 'day', 'week', 'month'")


class RateLimitStatusResponse(BaseModel):
    """Rate limit status for a tool"""
    tool_id: UUID
    tool_name: str
    rate_limits: List[Dict[str, Any]]
    current_usage: Dict[str, Any] = Field(..., description="Current usage by scope")
    status: str = Field(..., description="'ok', 'warning', 'exceeded'")


class AgentStatsResponse(BaseModel):
    """Statistics for a specific agent"""
    agent_id: str
    total_executions: int
    successful_executions: int
    failed_executions: int
    tools_used: int = Field(..., description="Number of unique tools used")
    total_cost: Optional[float] = None
    last_execution_at: Optional[datetime] = None


class RoleStatsResponse(BaseModel):
    """Statistics for a specific role"""
    role_id: UUID
    role_name: str
    total_executions: int
    successful_executions: int
    failed_executions: int
    tools_used: int = Field(..., description="Number of unique tools used")
    total_cost: Optional[float] = None
    last_execution_at: Optional[datetime] = None


class TopToolResponse(BaseModel):
    """Top tool by usage"""
    tool_id: UUID
    tool_name: str
    execution_count: int
    success_rate: float
    average_execution_time_ms: Optional[float] = None


class TopToolsResponse(BaseModel):
    """Response for top tools"""
    tools: List[TopToolResponse]
    period: Optional[str] = None
    limit: int = 10

