from sqlalchemy import (
    Column, String, Text, Boolean, Integer, 
    ForeignKey, Enum, Numeric, DateTime, JSON, UniqueConstraint
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship, validates
from datetime import datetime
import uuid
import enum

from app.database.database import Base


def enum_values(enum_cls):
    """Return enum values for SQLAlchemy Enum configuration."""
    return [member.value for member in enum_cls]


class ToolType(str, enum.Enum):
    """Tool type enumeration"""
    HTTP = "http"
    DATABASE = "database"


class ExecutionStatus(str, enum.Enum):
    """Execution status enumeration"""
    PENDING = "pending"
    RUNNING = "running"
    SUCCESS = "success"
    FAILED = "failed"


class RateLimitScope(str, enum.Enum):
    """Rate limit scope enumeration"""
    GLOBAL = "global"
    USER = "user"
    AGENT = "agent"


class PermissionAction(str, enum.Enum):
    """Permission action enumeration"""
    READ = "read"
    EXECUTE = "execute"
    MANAGE = "manage"


class ParameterType(str, enum.Enum):
    """Parameter type enumeration"""
    INPUT = "input"
    OUTPUT = "output"


class Tool(Base):
    """Tool registry table"""
    __tablename__ = "tools"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(255), unique=True, nullable=False, index=True)
    description = Column(Text, nullable=True)
    type = Column(Enum(ToolType, values_callable=enum_values), nullable=False)
    version = Column(String(50), nullable=False, default="1.0.0")
    is_active = Column(Boolean, default=True, nullable=False)
    tool_metadata = Column(JSON, nullable=True)  # Flexible JSONB for tool-specific data
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # Relationships
    parameters = relationship("ToolParameter", back_populates="tool", cascade="all, delete-orphan")
    configs = relationship("ToolConfig", back_populates="tool", cascade="all, delete-orphan")
    executions = relationship("ToolExecution", back_populates="tool", cascade="all, delete-orphan")
    rate_limits = relationship("ToolRateLimit", back_populates="tool", cascade="all, delete-orphan")
    permissions = relationship("ToolPermission", back_populates="tool", cascade="all, delete-orphan")

    @validates("type")
    def validate_type(self, key, value):
        if isinstance(value, ToolType):
            return value
        if isinstance(value, str):
            try:
                return ToolType(value.lower())
            except ValueError as exc:
                raise ValueError(f"Invalid tool type '{value}'") from exc
        raise TypeError("Tool type must be a ToolType or string")


class ToolParameter(Base):
    """Tool input/output parameter schemas"""
    __tablename__ = "tool_parameters"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tool_id = Column(UUID(as_uuid=True), ForeignKey("tools.id", ondelete="CASCADE"), nullable=False, index=True)
    name = Column(String(255), nullable=False)
    type = Column(String(50), nullable=False)  # 'string', 'number', 'boolean', 'object', etc.
    required = Column(Boolean, default=False, nullable=False)
    description = Column(Text, nullable=True)
    default_value = Column(Text, nullable=True)
    parameter_type = Column(Enum(ParameterType, values_callable=enum_values), nullable=False)  # 'input' or 'output'
    
    # Relationships
    tool = relationship("Tool", back_populates="parameters")


class ToolConfig(Base):
    """Tool-specific configurations"""
    __tablename__ = "tool_configs"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tool_id = Column(UUID(as_uuid=True), ForeignKey("tools.id", ondelete="CASCADE"), nullable=False, index=True)
    config_key = Column(String(255), nullable=False)
    config_value = Column(Text, nullable=True)  # Can store JSON strings or plain text
    
    # Relationships
    tool = relationship("Tool", back_populates="configs")
    
    # Unique constraint on tool_id + config_key
    __table_args__ = (
        UniqueConstraint("tool_id", "config_key", name="uq_tool_config"),
    )


class ToolExecution(Base):
    """Tool execution history"""
    __tablename__ = "tool_executions"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tool_id = Column(UUID(as_uuid=True), ForeignKey("tools.id", ondelete="CASCADE"), nullable=False, index=True)
    agent_id = Column(String(255), nullable=False, index=True)
    role_id = Column(UUID(as_uuid=True), ForeignKey("roles.id", ondelete="SET NULL"), nullable=True, index=True)
    status = Column(Enum(ExecutionStatus, values_callable=enum_values), nullable=False, default=ExecutionStatus.PENDING)
    input_data = Column(JSON, nullable=True)
    output_data = Column(JSON, nullable=True)
    error_message = Column(Text, nullable=True)
    execution_time_ms = Column(Integer, nullable=True)
    cost = Column(Numeric(10, 4), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    
    # Relationships
    tool = relationship("Tool", back_populates="executions")
    role = relationship("Role", back_populates="executions")


class ToolRateLimit(Base):
    """Rate limiting configuration per tool"""
    __tablename__ = "tool_rate_limits"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tool_id = Column(UUID(as_uuid=True), ForeignKey("tools.id", ondelete="CASCADE"), nullable=False, index=True)
    max_requests = Column(Integer, nullable=False)
    time_window_seconds = Column(Integer, nullable=False)
    scope = Column(Enum(RateLimitScope, values_callable=enum_values), nullable=False, default=RateLimitScope.GLOBAL)
    
    # Relationships
    tool = relationship("Tool", back_populates="rate_limits")


class Role(Base):
    """Role definitions"""
    __tablename__ = "roles"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(255), unique=True, nullable=False, index=True)
    description = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    # Relationships
    permissions = relationship("ToolPermission", back_populates="role", cascade="all, delete-orphan")
    executions = relationship("ToolExecution", back_populates="role")


class ToolPermission(Base):
    """Per-tool permissions linking tools to roles"""
    __tablename__ = "tool_permissions"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tool_id = Column(UUID(as_uuid=True), ForeignKey("tools.id", ondelete="CASCADE"), nullable=False, index=True)
    role_id = Column(UUID(as_uuid=True), ForeignKey("roles.id", ondelete="CASCADE"), nullable=False, index=True)
    action = Column(Enum(PermissionAction, values_callable=enum_values), nullable=False)
    granted = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    # Relationships
    tool = relationship("Tool", back_populates="permissions")
    role = relationship("Role", back_populates="permissions")
    
    # Unique constraint on tool_id + role_id + action
    __table_args__ = (
        UniqueConstraint("tool_id", "role_id", "action", name="uq_tool_permission"),
    )

