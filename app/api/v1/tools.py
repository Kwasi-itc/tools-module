from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from uuid import UUID

from app.database.database import get_db
from app.database.models import ToolType, ParameterType
from app.schemas.tool import (
    ToolCreate, ToolUpdate, ToolResponse, ToolDetailResponse,
    ToolParameterCreate, ToolParameterResponse,
    ToolConfigCreate, ToolConfigResponse,
    ToolListResponse
)
from app.services.tool_registry import ToolRegistryService

router = APIRouter(prefix="/tools", tags=["tools-management"])


@router.post("", response_model=ToolResponse, status_code=201)
async def create_tool(
    tool_data: ToolCreate,
    db: Session = Depends(get_db)
):
    """Create a new tool"""
    try:
        tool = ToolRegistryService.create_tool(db, tool_data)
        return tool
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error creating tool: {str(e)}")


@router.get("", response_model=ToolListResponse)
async def list_tools(
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(10, ge=1, le=100, description="Items per page"),
    search: Optional[str] = Query(None, description="Search in name and description"),
    tool_type: Optional[ToolType] = Query(None, description="Filter by tool type"),
    is_active: Optional[bool] = Query(None, description="Filter by active status"),
    db: Session = Depends(get_db)
):
    """List all tools with filtering and pagination"""
    skip = (page - 1) * page_size
    tools, total = ToolRegistryService.list_tools(
        db, skip=skip, limit=page_size, search=search,
        tool_type=tool_type, is_active=is_active
    )
    
    return ToolListResponse(
        tools=tools,
        total=total,
        page=page,
        page_size=page_size
    )


@router.get("/{tool_id}", response_model=ToolDetailResponse)
async def get_tool(
    tool_id: UUID,
    db: Session = Depends(get_db)
):
    """Get a tool by ID with all related data"""
    tool = ToolRegistryService.get_tool(db, tool_id)
    if not tool:
        raise HTTPException(status_code=404, detail="Tool not found")
    
    return tool


@router.put("/{tool_id}", response_model=ToolResponse)
async def update_tool(
    tool_id: UUID,
    tool_data: ToolUpdate,
    db: Session = Depends(get_db)
):
    """Update a tool"""
    try:
        tool = ToolRegistryService.update_tool(db, tool_id, tool_data)
        if not tool:
            raise HTTPException(status_code=404, detail="Tool not found")
        return tool
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error updating tool: {str(e)}")


@router.delete("/{tool_id}", status_code=204)
async def delete_tool(
    tool_id: UUID,
    hard_delete: bool = Query(False, description="Permanently delete instead of deactivating"),
    db: Session = Depends(get_db)
):
    """Delete (deactivate) a tool"""
    if hard_delete:
        success = ToolRegistryService.hard_delete_tool(db, tool_id)
    else:
        success = ToolRegistryService.delete_tool(db, tool_id)
    
    if not success:
        raise HTTPException(status_code=404, detail="Tool not found")
    
    return None


# Tool Parameters endpoints
@router.post("/{tool_id}/parameters", response_model=ToolParameterResponse, status_code=201)
async def add_parameter(
    tool_id: UUID,
    parameter_data: ToolParameterCreate,
    db: Session = Depends(get_db)
):
    """Add a parameter to a tool"""
    try:
        parameter = ToolRegistryService.add_parameter(db, tool_id, parameter_data)
        return parameter
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error adding parameter: {str(e)}")


@router.get("/{tool_id}/parameters", response_model=List[ToolParameterResponse])
async def get_parameters(
    tool_id: UUID,
    parameter_type: Optional[ParameterType] = Query(None, description="Filter by 'input' or 'output'"),
    db: Session = Depends(get_db)
):
    """Get all parameters for a tool"""
    # Verify tool exists
    tool = ToolRegistryService.get_tool(db, tool_id)
    if not tool:
        raise HTTPException(status_code=404, detail="Tool not found")
    
    parameters = ToolRegistryService.get_parameters(db, tool_id, parameter_type)
    return parameters


@router.delete("/parameters/{parameter_id}", status_code=204)
async def delete_parameter(
    parameter_id: UUID,
    db: Session = Depends(get_db)
):
    """Delete a parameter"""
    success = ToolRegistryService.delete_parameter(db, parameter_id)
    if not success:
        raise HTTPException(status_code=404, detail="Parameter not found")
    
    return None


# Tool Configs endpoints
@router.post("/{tool_id}/configs", response_model=ToolConfigResponse, status_code=201)
async def add_config(
    tool_id: UUID,
    config_data: ToolConfigCreate,
    db: Session = Depends(get_db)
):
    """Add or update a config for a tool"""
    try:
        config = ToolRegistryService.add_config(db, tool_id, config_data)
        return config
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error adding config: {str(e)}")


@router.get("/{tool_id}/configs", response_model=List[ToolConfigResponse])
async def get_configs(
    tool_id: UUID,
    db: Session = Depends(get_db)
):
    """Get all configs for a tool"""
    # Verify tool exists
    tool = ToolRegistryService.get_tool(db, tool_id)
    if not tool:
        raise HTTPException(status_code=404, detail="Tool not found")
    
    configs = ToolRegistryService.get_configs(db, tool_id)
    return configs


@router.get("/{tool_id}/configs/{config_key}", response_model=ToolConfigResponse)
async def get_config(
    tool_id: UUID,
    config_key: str,
    db: Session = Depends(get_db)
):
    """Get a specific config by key"""
    config = ToolRegistryService.get_config(db, tool_id, config_key)
    if not config:
        raise HTTPException(status_code=404, detail="Config not found")
    
    return config


@router.delete("/{tool_id}/configs/{config_key}", status_code=204)
async def delete_config(
    tool_id: UUID,
    config_key: str,
    db: Session = Depends(get_db)
):
    """Delete a config"""
    success = ToolRegistryService.delete_config(db, tool_id, config_key)
    if not success:
        raise HTTPException(status_code=404, detail="Config not found")
    
    return None

