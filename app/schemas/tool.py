from pydantic import BaseModel, Field, field_validator
from typing import Optional, List, Dict, Any, Literal
from datetime import datetime
from uuid import UUID
from app.database.models import ToolType, ParameterType


# Base schemas
class ToolParameterBase(BaseModel):
    name: str
    type: str = Field(..., description="Parameter type: string, number, boolean, object, array")
    required: bool = False
    description: Optional[str] = None
    default_value: Optional[str] = None
    parameter_type: Literal["input", "output"] = Field(..., description="Either 'input' or 'output'")


class ToolParameterCreate(ToolParameterBase):
    pass


class ToolParameterResponse(BaseModel):
    id: UUID
    tool_id: UUID
    name: str
    type: str
    required: bool
    description: Optional[str] = None
    default_value: Optional[str] = None
    parameter_type: ParameterType

    class Config:
        from_attributes = True
        use_enum_values = True


class ToolConfigBase(BaseModel):
    config_key: str
    config_value: Optional[str] = None


class ToolConfigCreate(ToolConfigBase):
    pass


class ToolConfigResponse(ToolConfigBase):
    id: UUID
    tool_id: UUID
    
    class Config:
        from_attributes = True


# Tool schemas
class ToolBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    type: ToolType
    version: str = Field(default="1.0.0", max_length=50)
    is_active: bool = True
    tool_metadata: Optional[Dict[str, Any]] = None

    @field_validator("type", mode="before")
    @classmethod
    def normalize_tool_type(cls, value: Any) -> ToolType:
        """Allow case-insensitive strings for tool type."""
        if isinstance(value, ToolType):
            return value
        if isinstance(value, str):
            try:
                return ToolType(value.lower())
            except ValueError as exc:
                raise ValueError(f"Invalid tool type '{value}'. Allowed values: {[t.value for t in ToolType]}") from exc
        raise TypeError("Tool type must be a ToolType or string value")


class ToolCreate(ToolBase):
    pass


class ToolUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None
    version: Optional[str] = Field(None, max_length=50)
    is_active: Optional[bool] = None
    tool_metadata: Optional[Dict[str, Any]] = None


class ToolResponse(ToolBase):
    id: UUID
    created_at: datetime
    updated_at: datetime
    parameters: List[ToolParameterResponse] = []
    
    class Config:
        from_attributes = True


class ToolDetailResponse(ToolResponse):
    """Tool with all related data"""
    configs: List[ToolConfigResponse] = []
    
    class Config:
        from_attributes = True


class ToolListResponse(BaseModel):
    """Response for listing tools"""
    tools: List[ToolResponse]
    total: int
    page: int = 1
    page_size: int = 10

