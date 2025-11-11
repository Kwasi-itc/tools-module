from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime
from uuid import UUID
from app.schemas.tool import ToolResponse, ToolListResponse


class RoleBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None


class RoleCreate(RoleBase):
    pass


class RoleUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None


class RoleResponse(RoleBase):
    id: UUID
    created_at: datetime
    
    class Config:
        from_attributes = True


class RoleListResponse(BaseModel):
    """Response for listing roles"""
    roles: List[RoleResponse]
    total: int
    page: int = 1
    page_size: int = 10


class RoleToolsResponse(BaseModel):
    """Response for tools accessible by a role"""
    role: RoleResponse
    tools: List[ToolResponse]
    total: int
    permission_action: str
    page: int = 1
    page_size: int = 100

