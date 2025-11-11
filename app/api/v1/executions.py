from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import Optional
from uuid import UUID

from app.database.database import get_db
from app.database.models import ExecutionStatus
from app.schemas.execution import (
    ExecutionRequest, ExecutionResponse, ExecutionDetailResponse,
    ExecutionListResponse
)
from sqlalchemy.orm import joinedload
from app.services.tool_executor import ToolExecutorService

router = APIRouter(prefix="/executions", tags=["tool-execution"])


@router.post("", response_model=ExecutionResponse, status_code=201)
async def execute_tool(
    execution_request: ExecutionRequest,
    db: Session = Depends(get_db)
):
    """
    Execute a tool.
    Requires EXECUTE permission for the role.
    Checks rate limits before execution.
    """
    try:
        execution = await ToolExecutorService.execute_tool(
            db=db,
            tool_id=execution_request.tool_id,
            agent_id=execution_request.agent_id,
            role_id=execution_request.role_id,
            input_data=execution_request.input_data
        )
        
        # Reload with tool relationship for tool_name
        from app.database.models import ToolExecution
        execution_with_tool = db.query(ToolExecution).options(
            joinedload(ToolExecution.tool)
        ).filter(ToolExecution.id == execution.id).first()
        
        return ExecutionResponse.from_orm_with_tool_name(execution_with_tool)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except PermissionError as e:
        raise HTTPException(status_code=403, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Execution failed: {str(e)}")


@router.get("/{execution_id}", response_model=ExecutionDetailResponse)
async def get_execution(
    execution_id: UUID,
    db: Session = Depends(get_db)
):
    """Get execution details by ID"""
    from app.database.models import ToolExecution
    execution = db.query(ToolExecution).options(
        joinedload(ToolExecution.tool)
    ).filter(ToolExecution.id == execution_id).first()
    
    if not execution:
        raise HTTPException(status_code=404, detail="Execution not found")
    
    return ExecutionResponse.from_orm_with_tool_name(execution)


@router.get("", response_model=ExecutionListResponse)
async def list_executions(
    tool_id: Optional[UUID] = Query(None, description="Filter by tool ID"),
    agent_id: Optional[str] = Query(None, description="Filter by agent ID"),
    role_id: Optional[UUID] = Query(None, description="Filter by role ID"),
    status: Optional[ExecutionStatus] = Query(None, description="Filter by status"),
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(10, ge=1, le=100, description="Items per page"),
    db: Session = Depends(get_db)
):
    """List execution history with filtering"""
    skip = (page - 1) * page_size
    executions, total = ToolExecutorService.list_executions(
        db,
        tool_id=tool_id,
        agent_id=agent_id,
        role_id=role_id,
        status=status,
        skip=skip,
        limit=page_size
    )
    
    # Convert to response format with tool names
    execution_responses = [
        ExecutionResponse.from_orm_with_tool_name(exec) for exec in executions
    ]
    
    return ExecutionListResponse(
        executions=execution_responses,
        total=total,
        page=page,
        page_size=page_size
    )


@router.get("/tool/{tool_id}", response_model=ExecutionListResponse)
async def get_tool_executions(
    tool_id: UUID,
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(10, ge=1, le=100, description="Items per page"),
    db: Session = Depends(get_db)
):
    """Get execution history for a specific tool"""
    skip = (page - 1) * page_size
    executions, total = ToolExecutorService.list_executions(
        db,
        tool_id=tool_id,
        skip=skip,
        limit=page_size
    )
    
    # Convert to response format with tool names
    execution_responses = [
        ExecutionResponse.from_orm_with_tool_name(exec) for exec in executions
    ]
    
    return ExecutionListResponse(
        executions=execution_responses,
        total=total,
        page=page,
        page_size=page_size
    )

