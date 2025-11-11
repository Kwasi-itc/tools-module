from sqlalchemy.orm import Session
from sqlalchemy import or_
from typing import List, Optional, Dict, Any
from uuid import UUID
from app.database.models import (
    Role, ToolPermission, Tool, PermissionAction
)
from app.schemas.permission import PermissionCreate, PermissionUpdate, BulkPermissionCreate
from app.schemas.role import RoleCreate, RoleUpdate


class PermissionManagementService:
    """Service for managing permissions and roles"""
    
    # Role Management
    @staticmethod
    def create_role(db: Session, role_data: RoleCreate) -> Role:
        """Create a new role"""
        # Check if role with same name exists
        existing = db.query(Role).filter(Role.name == role_data.name).first()
        if existing:
            raise ValueError(f"Role with name '{role_data.name}' already exists")
        
        role = Role(
            name=role_data.name,
            description=role_data.description
        )
        db.add(role)
        db.commit()
        db.refresh(role)
        return role
    
    @staticmethod
    def get_role(db: Session, role_id: UUID) -> Optional[Role]:
        """Get a role by ID"""
        return db.query(Role).filter(Role.id == role_id).first()
    
    @staticmethod
    def get_role_by_name(db: Session, name: str) -> Optional[Role]:
        """Get a role by name"""
        return db.query(Role).filter(Role.name == name).first()
    
    @staticmethod
    def list_roles(
        db: Session,
        skip: int = 0,
        limit: int = 10,
        search: Optional[str] = None
    ) -> tuple[List[Role], int]:
        """List roles with filtering and pagination"""
        query = db.query(Role)
        
        if search:
            search_filter = or_(
                Role.name.ilike(f"%{search}%"),
                Role.description.ilike(f"%{search}%")
            )
            query = query.filter(search_filter)
        
        total = query.count()
        roles = query.order_by(Role.name).offset(skip).limit(limit).all()
        
        return roles, total
    
    @staticmethod
    def update_role(db: Session, role_id: UUID, role_data: RoleUpdate) -> Optional[Role]:
        """Update a role"""
        role = db.query(Role).filter(Role.id == role_id).first()
        if not role:
            return None
        
        # Check name uniqueness if name is being updated
        if role_data.name and role_data.name != role.name:
            existing = db.query(Role).filter(
                Role.name == role_data.name,
                Role.id != role_id
            ).first()
            if existing:
                raise ValueError(f"Role with name '{role_data.name}' already exists")
        
        # Update fields
        update_data = role_data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(role, field, value)
        
        db.commit()
        db.refresh(role)
        return role
    
    @staticmethod
    def delete_role(db: Session, role_id: UUID) -> bool:
        """Delete a role"""
        role = db.query(Role).filter(Role.id == role_id).first()
        if not role:
            return False
        
        db.delete(role)
        db.commit()
        return True
    
    # Permission Management
    @staticmethod
    def create_permission(
        db: Session,
        permission_data: PermissionCreate
    ) -> ToolPermission:
        """Create a new permission"""
        # Verify tool exists
        tool = db.query(Tool).filter(Tool.id == permission_data.tool_id).first()
        if not tool:
            raise ValueError(f"Tool with id '{permission_data.tool_id}' not found")
        
        # Verify role exists
        role = db.query(Role).filter(Role.id == permission_data.role_id).first()
        if not role:
            raise ValueError(f"Role with id '{permission_data.role_id}' not found")
        
        # Check if permission already exists
        existing = db.query(ToolPermission).filter(
            ToolPermission.tool_id == permission_data.tool_id,
            ToolPermission.role_id == permission_data.role_id,
            ToolPermission.action == permission_data.action
        ).first()
        
        if existing:
            # Update existing permission
            existing.granted = permission_data.granted
            db.commit()
            db.refresh(existing)
            return existing
        
        # Create new permission
        permission = ToolPermission(
            tool_id=permission_data.tool_id,
            role_id=permission_data.role_id,
            action=permission_data.action,
            granted=permission_data.granted
        )
        db.add(permission)
        db.commit()
        db.refresh(permission)
        return permission
    
    @staticmethod
    def update_permission(
        db: Session,
        permission_id: UUID,
        permission_data: PermissionUpdate
    ) -> Optional[ToolPermission]:
        """Update a permission"""
        permission = db.query(ToolPermission).filter(
            ToolPermission.id == permission_id
        ).first()
        
        if not permission:
            return None
        
        update_data = permission_data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(permission, field, value)
        
        db.commit()
        db.refresh(permission)
        return permission
    
    @staticmethod
    def delete_permission(db: Session, permission_id: UUID) -> bool:
        """Delete a permission"""
        permission = db.query(ToolPermission).filter(
            ToolPermission.id == permission_id
        ).first()
        
        if not permission:
            return False
        
        db.delete(permission)
        db.commit()
        return True
    
    @staticmethod
    def list_permissions(
        db: Session,
        tool_id: Optional[UUID] = None,
        role_id: Optional[UUID] = None,
        action: Optional[PermissionAction] = None,
        granted: Optional[bool] = None,
        skip: int = 0,
        limit: int = 10
    ) -> tuple[List[ToolPermission], int]:
        """List permissions with filtering"""
        from sqlalchemy.orm import joinedload
        
        query = db.query(ToolPermission).options(
            joinedload(ToolPermission.tool),
            joinedload(ToolPermission.role)
        )
        
        if tool_id:
            query = query.filter(ToolPermission.tool_id == tool_id)
        if role_id:
            query = query.filter(ToolPermission.role_id == role_id)
        if action:
            query = query.filter(ToolPermission.action == action)
        if granted is not None:
            query = query.filter(ToolPermission.granted == granted)
        
        total = query.count()
        permissions = query.order_by(
            ToolPermission.created_at.desc()
        ).offset(skip).limit(limit).all()
        
        return permissions, total
    
    @staticmethod
    def create_bulk_permissions(
        db: Session,
        bulk_data: BulkPermissionCreate
    ) -> Dict[str, Any]:
        """Create permissions for multiple roles at once"""
        # Verify tool exists
        tool = db.query(Tool).filter(Tool.id == bulk_data.tool_id).first()
        if not tool:
            raise ValueError(f"Tool with id '{bulk_data.tool_id}' not found")
        
        created = 0
        updated = 0
        failed = 0
        permissions = []
        
        for role_id in bulk_data.role_ids:
            try:
                # Verify role exists
                role = db.query(Role).filter(Role.id == role_id).first()
                if not role:
                    failed += 1
                    continue
                
                # Check if permission already exists
                existing = db.query(ToolPermission).filter(
                    ToolPermission.tool_id == bulk_data.tool_id,
                    ToolPermission.role_id == role_id,
                    ToolPermission.action == bulk_data.action
                ).first()
                
                if existing:
                    existing.granted = bulk_data.granted
                    db.commit()
                    db.refresh(existing)
                    permissions.append(existing)
                    updated += 1
                else:
                    permission = ToolPermission(
                        tool_id=bulk_data.tool_id,
                        role_id=role_id,
                        action=bulk_data.action,
                        granted=bulk_data.granted
                    )
                    db.add(permission)
                    db.commit()
                    db.refresh(permission)
                    permissions.append(permission)
                    created += 1
            except Exception:
                failed += 1
                db.rollback()
        
        return {
            "created": created,
            "updated": updated,
            "failed": failed,
            "permissions": permissions
        }

