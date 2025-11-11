from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime
from uuid import UUID
from app.database.models import PermissionAction


class PermissionBase(BaseModel):
    """Base permission schema"""
    tool_id: UUID
    role_id: UUID
    action: PermissionAction
    granted: bool = True


class PermissionCreate(PermissionBase):
    """Schema for creating a permission"""
    pass


class PermissionUpdate(BaseModel):
    """Schema for updating a permission"""
    granted: Optional[bool] = None


class PermissionResponse(BaseModel):
    """Schema for permission response"""
    id: UUID
    tool_id: UUID
    role_id: UUID
    action: PermissionAction
    granted: bool
    created_at: datetime
    tool_name: Optional[str] = None
    role_name: Optional[str] = None
    
    class Config:
        from_attributes = True


class PermissionListResponse(BaseModel):
    """Response for listing permissions"""
    permissions: List[PermissionResponse]
    total: int
    page: int = 1
    page_size: int = 10


class BulkPermissionCreate(BaseModel):
    """Schema for creating multiple permissions at once"""
    tool_id: UUID
    role_ids: List[UUID] = Field(..., description="List of role IDs to grant permission to")
    action: PermissionAction
    granted: bool = True


class BulkPermissionResponse(BaseModel):
    """Response for bulk permission operations"""
    created: int
    updated: int
    failed: int
    permissions: List[PermissionResponse]

