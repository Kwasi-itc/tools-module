from pydantic import BaseModel, Field
from typing import Optional, Dict, Any
from datetime import datetime
from uuid import UUID
from app.database.models import ExecutionStatus


class ExecutionRequest(BaseModel):
    """Request to execute a tool"""
    tool_id: UUID = Field(..., description="ID of the tool to execute")
    agent_id: str = Field(..., description="ID of the agent/LLM requesting execution")
    role_id: UUID = Field(..., description="Role ID of the agent")
    input_data: Dict[str, Any] = Field(..., description="Input parameters for the tool")


class ExecutionResponse(BaseModel):
    """Response from tool execution"""
    id: UUID  # execution_id
    tool_id: UUID
    agent_id: str
    role_id: Optional[UUID]
    status: ExecutionStatus
    input_data: Optional[Dict[str, Any]] = None
    output_data: Optional[Dict[str, Any]] = None
    error_message: Optional[str] = None
    execution_time_ms: Optional[int] = None
    cost: Optional[float] = None
    created_at: datetime
    tool_name: Optional[str] = None  # Will be populated from relationship
    
    class Config:
        from_attributes = True
        
    @classmethod
    def from_orm_with_tool_name(cls, execution):
        """Create response with tool name from relationship"""
        data = {
            "id": execution.id,
            "tool_id": execution.tool_id,
            "agent_id": execution.agent_id,
            "role_id": execution.role_id,
            "status": execution.status,
            "input_data": execution.input_data,
            "output_data": execution.output_data,
            "error_message": execution.error_message,
            "execution_time_ms": execution.execution_time_ms,
            "cost": float(execution.cost) if execution.cost else None,
            "created_at": execution.created_at,
            "tool_name": execution.tool.name if execution.tool else None
        }
        return cls(**data)


class ExecutionDetailResponse(ExecutionResponse):
    """Detailed execution response with tool information"""
    pass


class ExecutionListResponse(BaseModel):
    """Response for listing executions"""
    executions: list[ExecutionResponse]
    total: int
    page: int = 1
    page_size: int = 10

