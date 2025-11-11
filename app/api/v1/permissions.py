from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import Optional, List
from uuid import UUID

from app.database.database import get_db
from app.database.models import PermissionAction
from app.schemas.permission import (
    PermissionCreate, PermissionUpdate, PermissionResponse,
    PermissionListResponse, BulkPermissionCreate, BulkPermissionResponse
)
from app.schemas.role import (
    RoleCreate, RoleUpdate, RoleResponse, RoleListResponse
)
from app.services.permission_management import PermissionManagementService
from sqlalchemy.orm import joinedload

router = APIRouter(prefix="/permissions", tags=["permissions-management"])


# Role Management Endpoints
@router.post("/roles", response_model=RoleResponse, status_code=201)
async def create_role(
    role_data: RoleCreate,
    db: Session = Depends(get_db)
):
    """Create a new role"""
    try:
        role = PermissionManagementService.create_role(db, role_data)
        return role
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error creating role: {str(e)}")


@router.get("/roles", response_model=RoleListResponse)
async def list_roles(
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(10, ge=1, le=100, description="Items per page"),
    search: Optional[str] = Query(None, description="Search in name and description"),
    db: Session = Depends(get_db)
):
    """List all roles with filtering and pagination"""
    skip = (page - 1) * page_size
    roles, total = PermissionManagementService.list_roles(
        db, skip=skip, limit=page_size, search=search
    )
    
    return RoleListResponse(
        roles=roles,
        total=total,
        page=page,
        page_size=page_size
    )


@router.get("/roles/{role_id}", response_model=RoleResponse)
async def get_role(
    role_id: UUID,
    db: Session = Depends(get_db)
):
    """Get a role by ID"""
    role = PermissionManagementService.get_role(db, role_id)
    if not role:
        raise HTTPException(status_code=404, detail="Role not found")
    
    return role


@router.put("/roles/{role_id}", response_model=RoleResponse)
async def update_role(
    role_id: UUID,
    role_data: RoleUpdate,
    db: Session = Depends(get_db)
):
    """Update a role"""
    try:
        role = PermissionManagementService.update_role(db, role_id, role_data)
        if not role:
            raise HTTPException(status_code=404, detail="Role not found")
        return role
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error updating role: {str(e)}")


@router.delete("/roles/{role_id}", status_code=204)
async def delete_role(
    role_id: UUID,
    db: Session = Depends(get_db)
):
    """Delete a role"""
    success = PermissionManagementService.delete_role(db, role_id)
    if not success:
        raise HTTPException(status_code=404, detail="Role not found")
    
    return None


# Permission Management Endpoints
@router.post("", response_model=PermissionResponse, status_code=201)
async def create_permission(
    permission_data: PermissionCreate,
    db: Session = Depends(get_db)
):
    """Create a new permission (grant access to a role for a tool)"""
    try:
        permission = PermissionManagementService.create_permission(db, permission_data)
        # Load relationships for response
        db.refresh(permission)
        from app.database.models import ToolPermission
        permission_with_relations = db.query(ToolPermission).options(
            joinedload(ToolPermission.tool),
            joinedload(ToolPermission.role)
        ).filter(ToolPermission.id == permission.id).first()
        
        return PermissionResponse(
            id=permission_with_relations.id,
            tool_id=permission_with_relations.tool_id,
            role_id=permission_with_relations.role_id,
            action=permission_with_relations.action,
            granted=permission_with_relations.granted,
            created_at=permission_with_relations.created_at,
            tool_name=permission_with_relations.tool.name if permission_with_relations.tool else None,
            role_name=permission_with_relations.role.name if permission_with_relations.role else None
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error creating permission: {str(e)}")


@router.post("/bulk", response_model=BulkPermissionResponse, status_code=201)
async def create_bulk_permissions(
    bulk_data: BulkPermissionCreate,
    db: Session = Depends(get_db)
):
    """Create permissions for multiple roles at once"""
    try:
        result = PermissionManagementService.create_bulk_permissions(db, bulk_data)
        
        # Format permissions for response
        from app.database.models import ToolPermission
        permission_responses = []
        for perm in result["permissions"]:
            perm_with_relations = db.query(ToolPermission).options(
                joinedload(ToolPermission.tool),
                joinedload(ToolPermission.role)
            ).filter(ToolPermission.id == perm.id).first()
            
            permission_responses.append(PermissionResponse(
                id=perm_with_relations.id,
                tool_id=perm_with_relations.tool_id,
                role_id=perm_with_relations.role_id,
                action=perm_with_relations.action,
                granted=perm_with_relations.granted,
                created_at=perm_with_relations.created_at,
                tool_name=perm_with_relations.tool.name if perm_with_relations.tool else None,
                role_name=perm_with_relations.role.name if perm_with_relations.role else None
            ))
        
        return BulkPermissionResponse(
            created=result["created"],
            updated=result["updated"],
            failed=result["failed"],
            permissions=permission_responses
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error creating bulk permissions: {str(e)}")


@router.get("", response_model=PermissionListResponse)
async def list_permissions(
    tool_id: Optional[UUID] = Query(None, description="Filter by tool ID"),
    role_id: Optional[UUID] = Query(None, description="Filter by role ID"),
    action: Optional[PermissionAction] = Query(None, description="Filter by action"),
    granted: Optional[bool] = Query(None, description="Filter by granted status"),
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(10, ge=1, le=100, description="Items per page"),
    db: Session = Depends(get_db)
):
    """List permissions with filtering"""
    skip = (page - 1) * page_size
    permissions, total = PermissionManagementService.list_permissions(
        db,
        tool_id=tool_id,
        role_id=role_id,
        action=action,
        granted=granted,
        skip=skip,
        limit=page_size
    )
    
    # Format permissions for response
    permission_responses = []
    for perm in permissions:
        permission_responses.append(PermissionResponse(
            id=perm.id,
            tool_id=perm.tool_id,
            role_id=perm.role_id,
            action=perm.action,
            granted=perm.granted,
            created_at=perm.created_at,
            tool_name=perm.tool.name if perm.tool else None,
            role_name=perm.role.name if perm.role else None
        ))
    
    return PermissionListResponse(
        permissions=permission_responses,
        total=total,
        page=page,
        page_size=page_size
    )


@router.get("/tool/{tool_id}", response_model=PermissionListResponse)
async def get_tool_permissions(
    tool_id: UUID,
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(10, ge=1, le=100, description="Items per page"),
    db: Session = Depends(get_db)
):
    """Get all permissions for a specific tool"""
    skip = (page - 1) * page_size
    permissions, total = PermissionManagementService.list_permissions(
        db,
        tool_id=tool_id,
        skip=skip,
        limit=page_size
    )
    
    # Format permissions for response
    permission_responses = []
    for perm in permissions:
        permission_responses.append(PermissionResponse(
            id=perm.id,
            tool_id=perm.tool_id,
            role_id=perm.role_id,
            action=perm.action,
            granted=perm.granted,
            created_at=perm.created_at,
            tool_name=perm.tool.name if perm.tool else None,
            role_name=perm.role.name if perm.role else None
        ))
    
    return PermissionListResponse(
        permissions=permission_responses,
        total=total,
        page=page,
        page_size=page_size
    )


@router.get("/role/{role_id}", response_model=PermissionListResponse)
async def get_role_permissions(
    role_id: UUID,
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(10, ge=1, le=100, description="Items per page"),
    db: Session = Depends(get_db)
):
    """Get all permissions for a specific role"""
    skip = (page - 1) * page_size
    permissions, total = PermissionManagementService.list_permissions(
        db,
        role_id=role_id,
        skip=skip,
        limit=page_size
    )
    
    # Format permissions for response
    permission_responses = []
    for perm in permissions:
        permission_responses.append(PermissionResponse(
            id=perm.id,
            tool_id=perm.tool_id,
            role_id=perm.role_id,
            action=perm.action,
            granted=perm.granted,
            created_at=perm.created_at,
            tool_name=perm.tool.name if perm.tool else None,
            role_name=perm.role.name if perm.role else None
        ))
    
    return PermissionListResponse(
        permissions=permission_responses,
        total=total,
        page=page,
        page_size=page_size
    )


@router.put("/{permission_id}", response_model=PermissionResponse)
async def update_permission(
    permission_id: UUID,
    permission_data: PermissionUpdate,
    db: Session = Depends(get_db)
):
    """Update a permission (grant/revoke)"""
    permission = PermissionManagementService.update_permission(
        db, permission_id, permission_data
    )
    if not permission:
        raise HTTPException(status_code=404, detail="Permission not found")
    
    # Load relationships for response
    from app.database.models import ToolPermission
    permission_with_relations = db.query(ToolPermission).options(
        joinedload(ToolPermission.tool),
        joinedload(ToolPermission.role)
    ).filter(ToolPermission.id == permission.id).first()
    
    return PermissionResponse(
        id=permission_with_relations.id,
        tool_id=permission_with_relations.tool_id,
        role_id=permission_with_relations.role_id,
        action=permission_with_relations.action,
        granted=permission_with_relations.granted,
        created_at=permission_with_relations.created_at,
        tool_name=permission_with_relations.tool.name if permission_with_relations.tool else None,
        role_name=permission_with_relations.role.name if permission_with_relations.role else None
    )


@router.delete("/{permission_id}", status_code=204)
async def delete_permission(
    permission_id: UUID,
    db: Session = Depends(get_db)
):
    """Delete (revoke) a permission"""
    success = PermissionManagementService.delete_permission(db, permission_id)
    if not success:
        raise HTTPException(status_code=404, detail="Permission not found")
    
    return None

