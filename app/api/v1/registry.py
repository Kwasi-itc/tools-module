from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from uuid import UUID

from app.database.database import get_db
from app.database.models import PermissionAction, Tool
from app.schemas.tool import ToolListResponse
from app.services.tool_registry import ToolRegistryService
from app.api.v1.tools import _enhance_tool_description

router = APIRouter(prefix="/registry", tags=["tools-registry"])


@router.get("/by-role/{role_id}", response_model=ToolListResponse)
async def get_tools_by_role(
    role_id: UUID,
    permission_action: PermissionAction = Query(
        PermissionAction.READ,
        description="Minimum permission level: read, execute, or manage"
    ),
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(100, ge=1, le=100, description="Items per page"),
    db: Session = Depends(get_db)
):
    """
    Get all tools that a role has access to.
    Returns tools where the role has the specified permission level or higher.
    This is the main endpoint for agents/LLMs to discover available tools.
    """
    skip = (page - 1) * page_size
    tools, total = ToolRegistryService.get_tools_by_role(
        db, role_id, permission_action, skip, page_size
    )
    
    # Enhance descriptions with Args section for LLM consumption
    for tool in tools:
        tool.description = _enhance_tool_description(tool)
    
    return ToolListResponse(
        tools=tools,
        total=total,
        page=page,
        page_size=page_size
    )


@router.get("/by-role-name/{role_name}", response_model=ToolListResponse)
async def get_tools_by_role_name(
    role_name: str,
    permission_action: PermissionAction = Query(
        PermissionAction.READ,
        description="Minimum permission level: read, execute, or manage"
    ),
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(100, ge=1, le=100, description="Items per page"),
    db: Session = Depends(get_db)
):
    """
    Get all tools that a role has access to by role name.
    Returns tools where the role has the specified permission level or higher.
    Convenient endpoint when you know the role name but not the ID.
    """
    skip = (page - 1) * page_size
    tools, total = ToolRegistryService.get_tools_by_role_name(
        db, role_name, permission_action, skip, page_size
    )
    
    # Enhance descriptions with Args section for LLM consumption
    for tool in tools:
        tool.description = _enhance_tool_description(tool)
    
    return ToolListResponse(
        tools=tools,
        total=total,
        page=page,
        page_size=page_size
    )


@router.get("/check-permission/{tool_id}/{role_id}")
async def check_tool_permission(
    tool_id: UUID,
    role_id: UUID,
    required_action: PermissionAction = Query(
        PermissionAction.EXECUTE,
        description="Required permission level: read, execute, or manage"
    ),
    db: Session = Depends(get_db)
):
    """
    Check if a role has the required permission for a specific tool.
    Returns True if role has the required permission or higher.
    Useful for validating access before tool execution.
    """
    # Verify tool exists
    tool = ToolRegistryService.get_tool(db, tool_id)
    if not tool:
        raise HTTPException(status_code=404, detail="Tool not found")
    
    has_permission = ToolRegistryService.check_tool_permission(
        db, tool_id, role_id, required_action
    )
    
    return {
        "tool_id": str(tool_id),
        "role_id": str(role_id),
        "required_action": required_action.value,
        "has_permission": has_permission
    }

