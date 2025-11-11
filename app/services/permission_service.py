from sqlalchemy.orm import Session
from uuid import UUID
from app.database.models import ToolPermission, PermissionAction


class PermissionService:
    """Service for checking permissions"""
    
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

