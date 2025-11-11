from sqlalchemy.orm import Session
from typing import Dict, Any, Optional
from uuid import UUID
from datetime import datetime
import time

from app.database.models import (
    Tool, ToolExecution, ExecutionStatus, ToolType
)
from app.schemas.execution import ExecutionResponse
from app.executors.http_executor import HTTPExecutor
from app.executors.database_executor import DatabaseExecutor
from app.services.tool_registry import ToolRegistryService
from app.services.permission_service import PermissionService
from app.services.rate_limit_service import RateLimitService
from app.database.models import PermissionAction
from app.config import settings


class ToolExecutorService:
    """Service for executing tools"""
    
    @staticmethod
    async def execute_tool(
        db: Session,
        tool_id: UUID,
        agent_id: str,
        role_id: UUID,
        input_data: Dict[str, Any]
    ) -> ToolExecution:
        """
        Execute a tool with permission and rate limit checks.
        
        Args:
            db: Database session
            tool_id: ID of the tool to execute
            agent_id: ID of the agent requesting execution
            role_id: Role ID of the agent
            input_data: Input parameters for the tool
            
        Returns:
            ToolExecution record
        """
        # Get the tool
        tool = ToolRegistryService.get_tool(db, tool_id)
        if not tool:
            raise ValueError(f"Tool with id '{tool_id}' not found")
        
        if not tool.is_active:
            raise ValueError(f"Tool '{tool.name}' is not active")
        
        # Check permission
        has_permission = PermissionService.check_tool_permission(
            db, tool_id, role_id, PermissionAction.EXECUTE
        )
        if not has_permission:
            raise PermissionError(
                f"Role does not have EXECUTE permission for tool '{tool.name}'"
            )
        
        # Check rate limits
        rate_limit_check = RateLimitService.check_rate_limit(
            db, tool_id, agent_id, role_id
        )
        if not rate_limit_check["allowed"]:
            raise ValueError(
                f"Rate limit exceeded: {rate_limit_check.get('message', 'Too many requests')}"
            )
        
        # Create execution record
        execution = ToolExecution(
            tool_id=tool_id,
            agent_id=agent_id,
            role_id=role_id,
            status=ExecutionStatus.PENDING,
            input_data=input_data
        )
        db.add(execution)
        db.commit()
        db.refresh(execution)
        
        # Execute the tool
        start_time = time.time()
        execution.status = ExecutionStatus.RUNNING
        db.commit()
        
        try:
            if tool.type == ToolType.HTTP:
                result = await HTTPExecutor.execute(
                    tool, input_data, settings.default_execution_timeout_seconds
                )
                output_data = result
                
            elif tool.type == ToolType.DATABASE:
                result = DatabaseExecutor.execute(
                    tool, input_data, db, settings.default_execution_timeout_seconds
                )
                output_data = result
            else:
                raise ValueError(f"Unsupported tool type: {tool.type}")
            
            # Calculate execution time
            execution_time_ms = int((time.time() - start_time) * 1000)
            
            # Update execution record
            execution.status = ExecutionStatus.SUCCESS
            execution.output_data = output_data
            execution.execution_time_ms = execution_time_ms
            execution.error_message = None
            
            # Record rate limit usage
            RateLimitService.record_usage(db, tool_id, agent_id, role_id)
            
        except Exception as e:
            execution_time_ms = int((time.time() - start_time) * 1000)
            execution.status = ExecutionStatus.FAILED
            execution.error_message = str(e)
            execution.execution_time_ms = execution_time_ms
            execution.output_data = None
        
        db.commit()
        db.refresh(execution)
        
        return execution
    
    @staticmethod
    def get_execution(
        db: Session,
        execution_id: UUID
    ) -> Optional[ToolExecution]:
        """Get an execution record by ID"""
        return db.query(ToolExecution).filter(
            ToolExecution.id == execution_id
        ).first()
    
    @staticmethod
    def list_executions(
        db: Session,
        tool_id: Optional[UUID] = None,
        agent_id: Optional[str] = None,
        role_id: Optional[UUID] = None,
        status: Optional[ExecutionStatus] = None,
        skip: int = 0,
        limit: int = 10
    ) -> tuple[list[ToolExecution], int]:
        """List execution records with filtering"""
        from sqlalchemy.orm import joinedload
        
        query = db.query(ToolExecution).options(joinedload(ToolExecution.tool))
        
        if tool_id:
            query = query.filter(ToolExecution.tool_id == tool_id)
        if agent_id:
            query = query.filter(ToolExecution.agent_id == agent_id)
        if role_id:
            query = query.filter(ToolExecution.role_id == role_id)
        if status:
            query = query.filter(ToolExecution.status == status)
        
        total = query.count()
        executions = query.order_by(
            ToolExecution.created_at.desc()
        ).offset(skip).limit(limit).all()
        
        return executions, total

