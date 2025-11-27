from sqlalchemy.orm import Session, joinedload
from sqlalchemy import or_, func
from typing import List, Optional, Dict, Any
from uuid import UUID
from app.database.models import (
    Tool, ToolParameter, ToolConfig, ToolType, ParameterType,
    Role, ToolPermission, PermissionAction
)
from app.schemas.tool import (
    ToolCreate, ToolUpdate, ToolParameterCreate, ToolConfigCreate
)


class ToolRegistryService:
    """Service for managing tool registry"""
    
    @staticmethod
    def create_tool(db: Session, tool_data: ToolCreate) -> Tool:
        """Create a new tool"""
        # Check if tool with same name exists
        existing = db.query(Tool).filter(Tool.name == tool_data.name).first()
        if existing:
            raise ValueError(f"Tool with name '{tool_data.name}' already exists")
        
        tool_type = tool_data.type
        if isinstance(tool_type, str):
            tool_type = ToolType(tool_type.lower())

        tool = Tool(
            name=tool_data.name,
            description=tool_data.description,
            type=tool_type,
            version=tool_data.version,
            is_active=tool_data.is_active,
            tool_metadata=tool_data.tool_metadata
        )
        db.add(tool)
        db.commit()
        db.refresh(tool)
        return tool
    
    @staticmethod
    def get_tool(db: Session, tool_id: UUID) -> Optional[Tool]:
        """Get a tool by ID with parameters and configs eagerly loaded"""
        from sqlalchemy.orm import joinedload
        return db.query(Tool).options(
            joinedload(Tool.parameters),
            joinedload(Tool.configs)
        ).filter(Tool.id == tool_id).first()
    
    @staticmethod
    def get_tool_by_name(db: Session, name: str) -> Optional[Tool]:
        """Get a tool by name"""
        return db.query(Tool).filter(Tool.name == name).first()
    
    @staticmethod
    def list_tools(
        db: Session,
        skip: int = 0,
        limit: int = 10,
        search: Optional[str] = None,
        tool_type: Optional[ToolType] = None,
        is_active: Optional[bool] = None
    ) -> tuple[List[Tool], int]:
        """List tools with filtering and pagination"""
        query = db.query(Tool)
        
        # Apply filters
        if search:
            search_filter = or_(
                Tool.name.ilike(f"%{search}%"),
                Tool.description.ilike(f"%{search}%")
            )
            query = query.filter(search_filter)
        
        if tool_type:
            query = query.filter(Tool.type == tool_type)
        
        if is_active is not None:
            query = query.filter(Tool.is_active == is_active)
        
        # Get total count
        total = query.count()
        
        # Eager load parameters and configs for each tool
        query = query.options(
            joinedload(Tool.parameters),
            joinedload(Tool.configs)
        )
        
        # Apply pagination
        tools = query.order_by(Tool.created_at.desc()).offset(skip).limit(limit).all()
        
        return tools, total
    
    @staticmethod
    def update_tool(db: Session, tool_id: UUID, tool_data: ToolUpdate) -> Optional[Tool]:
        """Update a tool"""
        tool = db.query(Tool).filter(Tool.id == tool_id).first()
        if not tool:
            return None
        
        # Check name uniqueness if name is being updated
        if tool_data.name and tool_data.name != tool.name:
            existing = db.query(Tool).filter(
                Tool.name == tool_data.name,
                Tool.id != tool_id
            ).first()
            if existing:
                raise ValueError(f"Tool with name '{tool_data.name}' already exists")
        
        # Update fields
        update_data = tool_data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(tool, field, value)
        
        db.commit()
        db.refresh(tool)
        return tool
    
    @staticmethod
    def delete_tool(db: Session, tool_id: UUID) -> bool:
        """Delete (deactivate) a tool"""
        tool = db.query(Tool).filter(Tool.id == tool_id).first()
        if not tool:
            return False
        
        # Soft delete by deactivating
        tool.is_active = False
        db.commit()
        return True
    
    @staticmethod
    def hard_delete_tool(db: Session, tool_id: UUID) -> bool:
        """Permanently delete a tool and all related data"""
        tool = db.query(Tool).filter(Tool.id == tool_id).first()
        if not tool:
            return False
        
        db.delete(tool)
        db.commit()
        return True
    
    # Tool Parameter methods
    @staticmethod
    def add_parameter(
        db: Session,
        tool_id: UUID,
        parameter_data: ToolParameterCreate
    ) -> ToolParameter:
        """Add a parameter to a tool"""
        tool = db.query(Tool).filter(Tool.id == tool_id).first()
        if not tool:
            raise ValueError(f"Tool with id '{tool_id}' not found")
        
        # Convert string to enum if needed
        param_type_enum = ParameterType.INPUT if parameter_data.parameter_type == "input" else ParameterType.OUTPUT
        
        # Check if parameter with same name and type already exists
        existing = db.query(ToolParameter).filter(
            ToolParameter.tool_id == tool_id,
            ToolParameter.name == parameter_data.name,
            ToolParameter.parameter_type == param_type_enum
        ).first()
        if existing:
            raise ValueError(
                f"Parameter '{parameter_data.name}' of type '{parameter_data.parameter_type}' "
                f"already exists for this tool"
            )
        
        parameter = ToolParameter(
            tool_id=tool_id,
            name=parameter_data.name,
            type=parameter_data.type,
            required=parameter_data.required,
            description=parameter_data.description,
            default_value=parameter_data.default_value,
            parameter_type=param_type_enum
        )
        db.add(parameter)
        db.commit()
        db.refresh(parameter)
        return parameter
    
    @staticmethod
    def get_parameters(
        db: Session,
        tool_id: UUID,
        parameter_type: Optional[ParameterType] = None
    ) -> List[ToolParameter]:
        """Get parameters for a tool"""
        query = db.query(ToolParameter).filter(ToolParameter.tool_id == tool_id)
        
        if parameter_type:
            query = query.filter(ToolParameter.parameter_type == parameter_type)
        
        return query.order_by(ToolParameter.name).all()
    
    @staticmethod
    def delete_parameter(db: Session, parameter_id: UUID) -> bool:
        """Delete a parameter"""
        parameter = db.query(ToolParameter).filter(ToolParameter.id == parameter_id).first()
        if not parameter:
            return False
        
        db.delete(parameter)
        db.commit()
        return True
    
    # Tool Config methods
    @staticmethod
    def add_config(
        db: Session,
        tool_id: UUID,
        config_data: ToolConfigCreate
    ) -> ToolConfig:
        """Add or update a config for a tool"""
        tool = db.query(Tool).filter(Tool.id == tool_id).first()
        if not tool:
            raise ValueError(f"Tool with id '{tool_id}' not found")
        
        # Check if config already exists
        existing = db.query(ToolConfig).filter(
            ToolConfig.tool_id == tool_id,
            ToolConfig.config_key == config_data.config_key
        ).first()
        
        if existing:
            # Update existing config
            existing.config_value = config_data.config_value
            db.commit()
            db.refresh(existing)
            return existing
        else:
            # Create new config
            config = ToolConfig(
                tool_id=tool_id,
                config_key=config_data.config_key,
                config_value=config_data.config_value
            )
            db.add(config)
            db.commit()
            db.refresh(config)
            return config
    
    @staticmethod
    def get_configs(db: Session, tool_id: UUID) -> List[ToolConfig]:
        """Get all configs for a tool"""
        return db.query(ToolConfig).filter(
            ToolConfig.tool_id == tool_id
        ).order_by(ToolConfig.config_key).all()
    
    @staticmethod
    def get_config(db: Session, tool_id: UUID, config_key: str) -> Optional[ToolConfig]:
        """Get a specific config by key"""
        return db.query(ToolConfig).filter(
            ToolConfig.tool_id == tool_id,
            ToolConfig.config_key == config_key
        ).first()
    
    @staticmethod
    def delete_config(db: Session, tool_id: UUID, config_key: str) -> bool:
        """Delete a config"""
        config = db.query(ToolConfig).filter(
            ToolConfig.tool_id == tool_id,
            ToolConfig.config_key == config_key
        ).first()
        if not config:
            return False
        
        db.delete(config)
        db.commit()
        return True
    
    # Role-based tool access methods
    @staticmethod
    def get_tools_by_role(
        db: Session,
        role_id: UUID,
        permission_action: Optional[PermissionAction] = PermissionAction.READ,
        skip: int = 0,
        limit: int = 100
    ) -> tuple[List[Tool], int]:
        """
        Get tools that a role has access to based on permissions.
        By default returns tools with READ permission or higher.
        """
        # Get all permissions for this role with the specified action (or higher)
        # MANAGE > EXECUTE > READ hierarchy
        if permission_action == PermissionAction.READ:
            # Get tools with READ, EXECUTE, or MANAGE permissions
            allowed_actions = [
                PermissionAction.READ,
                PermissionAction.EXECUTE,
                PermissionAction.MANAGE
            ]
        elif permission_action == PermissionAction.EXECUTE:
            # Get tools with EXECUTE or MANAGE permissions
            allowed_actions = [
                PermissionAction.EXECUTE,
                PermissionAction.MANAGE
            ]
        else:  # MANAGE
            # Only get tools with MANAGE permission
            allowed_actions = [PermissionAction.MANAGE]
        
        # Query tools that have permissions for this role
        # Use distinct on ID, but must order by ID first for PostgreSQL
        query = db.query(Tool).join(
            ToolPermission,
            Tool.id == ToolPermission.tool_id
        ).filter(
            ToolPermission.role_id == role_id,
            ToolPermission.action.in_(allowed_actions),
            ToolPermission.granted == True,
            Tool.is_active == True
        ).distinct(Tool.id).order_by(Tool.id, Tool.name)
        
        # Get total count - use subquery with distinct on ID to avoid JSON comparison issues
        total = db.query(Tool.id).join(
            ToolPermission,
            Tool.id == ToolPermission.tool_id
        ).filter(
            ToolPermission.role_id == role_id,
            ToolPermission.action.in_(allowed_actions),
            ToolPermission.granted == True,
            Tool.is_active == True
        ).distinct().count()
        
        # Eager load parameters and configs for each tool
        query = query.options(
            joinedload(Tool.parameters),
            joinedload(Tool.configs)
        )
        
        # Apply pagination - note: ordering is already set above
        tools = query.offset(skip).limit(limit).all()
        
        # Sort results by name in Python after fetching to maintain name ordering
        tools = sorted(tools, key=lambda t: t.name)
        
        return tools, total
    
    @staticmethod
    def get_tools_by_role_name(
        db: Session,
        role_name: str,
        permission_action: Optional[PermissionAction] = PermissionAction.READ,
        skip: int = 0,
        limit: int = 100
    ) -> tuple[List[Tool], int]:
        """
        Get tools that a role has access to by role name.
        """
        # First get the role by name
        role = db.query(Role).filter(Role.name == role_name).first()
        if not role:
            return [], 0
        
        return ToolRegistryService.get_tools_by_role(
            db, role.id, permission_action, skip, limit
        )
    
    @staticmethod
    def check_tool_permission(
        db: Session,
        tool_id: UUID,
        role_id: UUID,
        required_action: PermissionAction
    ) -> bool:
        """
        Check if a role has the required permission for a tool.
        Returns True if role has the required action or higher.
        """
        # Get all permissions for this tool and role
        permissions = db.query(ToolPermission).filter(
            ToolPermission.tool_id == tool_id,
            ToolPermission.role_id == role_id,
            ToolPermission.granted == True
        ).all()
        
        if not permissions:
            return False
        
        # Check if any permission meets the requirement
        action_hierarchy = {
            PermissionAction.READ: 1,
            PermissionAction.EXECUTE: 2,
            PermissionAction.MANAGE: 3
        }
        
        required_level = action_hierarchy[required_action]
        
        for perm in permissions:
            perm_level = action_hierarchy[perm.action]
            if perm_level >= required_level:
                return True
        
        return False

