from sqlalchemy.orm import Session
from sqlalchemy import func, and_, or_, case
from typing import Dict, Any, List, Optional
from uuid import UUID
from datetime import datetime, timedelta
from app.database.models import (
    Tool, ToolExecution, ToolRateLimit, ExecutionStatus,
    RateLimitScope
)
from app.schemas.analytics import (
    ToolStatsResponse, ExecutionStatsResponse, TimeSeriesDataPoint,
    ToolUsageStatsResponse, RateLimitStatusResponse, AgentStatsResponse,
    RoleStatsResponse, TopToolResponse
)


class AnalyticsService:
    """Service for analytics and monitoring"""
    
    @staticmethod
    def get_tool_stats(
        db: Session,
        tool_id: UUID
    ) -> Optional[ToolStatsResponse]:
        """Get statistics for a specific tool"""
        tool = db.query(Tool).filter(Tool.id == tool_id).first()
        if not tool:
            return None
        
        # Get execution statistics
        stats = db.query(
            func.count(ToolExecution.id).label('total'),
            func.sum(case((ToolExecution.status == ExecutionStatus.SUCCESS, 1), else_=0)).label('successful'),
            func.sum(case((ToolExecution.status == ExecutionStatus.FAILED, 1), else_=0)).label('failed'),
            func.avg(ToolExecution.execution_time_ms).label('avg_time'),
            func.sum(ToolExecution.cost).label('total_cost'),
            func.max(ToolExecution.created_at).label('last_execution')
        ).filter(
            ToolExecution.tool_id == tool_id
        ).first()
        
        total = stats.total or 0
        successful = stats.successful or 0
        failed = stats.failed or 0
        success_rate = (successful / total * 100) if total > 0 else 0.0
        
        return ToolStatsResponse(
            tool_id=tool_id,
            tool_name=tool.name,
            total_executions=total,
            successful_executions=successful,
            failed_executions=failed,
            success_rate=round(success_rate, 2),
            average_execution_time_ms=float(stats.avg_time) if stats.avg_time else None,
            total_cost=float(stats.total_cost) if stats.total_cost else None,
            last_execution_at=stats.last_execution
        )
    
    @staticmethod
    def get_execution_stats(db: Session) -> ExecutionStatsResponse:
        """Get overall execution statistics"""
        stats = db.query(
            func.count(ToolExecution.id).label('total'),
            func.sum(case((ToolExecution.status == ExecutionStatus.SUCCESS, 1), else_=0)).label('successful'),
            func.sum(case((ToolExecution.status == ExecutionStatus.FAILED, 1), else_=0)).label('failed'),
            func.sum(case((ToolExecution.status == ExecutionStatus.PENDING, 1), else_=0)).label('pending'),
            func.sum(case((ToolExecution.status == ExecutionStatus.RUNNING, 1), else_=0)).label('running'),
            func.avg(ToolExecution.execution_time_ms).label('avg_time'),
            func.sum(ToolExecution.cost).label('total_cost')
        ).first()
        
        total = stats.total or 0
        successful = stats.successful or 0
        success_rate = (successful / total * 100) if total > 0 else 0.0
        
        return ExecutionStatsResponse(
            total_executions=total,
            successful_executions=successful,
            failed_executions=stats.failed or 0,
            pending_executions=stats.pending or 0,
            running_executions=stats.running or 0,
            success_rate=round(success_rate, 2),
            average_execution_time_ms=float(stats.avg_time) if stats.avg_time else None,
            total_cost=float(stats.total_cost) if stats.total_cost else None
        )
    
    @staticmethod
    def get_tool_usage_stats(
        db: Session,
        tool_id: UUID,
        period: str = "day",
        days: int = 7
    ) -> Optional[ToolUsageStatsResponse]:
        """Get tool usage statistics over time"""
        tool = db.query(Tool).filter(Tool.id == tool_id).first()
        if not tool:
            return None
        
        # Calculate time range
        end_time = datetime.utcnow()
        start_time = end_time - timedelta(days=days)
        
        # Group by time period
        if period == "hour":
            time_format = func.date_trunc('hour', ToolExecution.created_at)
            interval = timedelta(hours=1)
        elif period == "day":
            time_format = func.date_trunc('day', ToolExecution.created_at)
            interval = timedelta(days=1)
        elif period == "week":
            time_format = func.date_trunc('week', ToolExecution.created_at)
            interval = timedelta(weeks=1)
        else:  # month
            time_format = func.date_trunc('month', ToolExecution.created_at)
            interval = timedelta(days=30)
        
        # Query execution counts by time period
        results = db.query(
            time_format.label('timestamp'),
            func.count(ToolExecution.id).label('count')
        ).filter(
            ToolExecution.tool_id == tool_id,
            ToolExecution.created_at >= start_time,
            ToolExecution.created_at <= end_time
        ).group_by(
            time_format
        ).order_by(
            time_format
        ).all()
        
        time_series = [
            TimeSeriesDataPoint(
                timestamp=row.timestamp,
                value=float(row.count),
                label=f"Executions"
            )
            for row in results
        ]
        
        return ToolUsageStatsResponse(
            tool_id=tool_id,
            tool_name=tool.name,
            time_series=time_series,
            period=period
        )
    
    @staticmethod
    def get_rate_limit_status(
        db: Session,
        tool_id: UUID,
        agent_id: Optional[str] = None,
        role_id: Optional[UUID] = None
    ) -> Optional[RateLimitStatusResponse]:
        """Get rate limit status for a tool"""
        tool = db.query(Tool).filter(Tool.id == tool_id).first()
        if not tool:
            return None
        
        # Get rate limits
        rate_limits = db.query(ToolRateLimit).filter(
            ToolRateLimit.tool_id == tool_id
        ).all()
        
        rate_limit_configs = []
        current_usage = {}
        status = "ok"
        
        for rate_limit in rate_limits:
            # Calculate current usage
            window_start = datetime.utcnow() - timedelta(
                seconds=rate_limit.time_window_seconds
            )
            
            query = db.query(func.count(ToolExecution.id)).filter(
                ToolExecution.tool_id == tool_id,
                ToolExecution.created_at >= window_start,
                ToolExecution.status.in_([ExecutionStatus.SUCCESS, ExecutionStatus.FAILED])
            )
            
            if rate_limit.scope == RateLimitScope.AGENT and agent_id:
                query = query.filter(ToolExecution.agent_id == agent_id)
            elif rate_limit.scope == RateLimitScope.USER and role_id:
                query = query.filter(ToolExecution.role_id == role_id)
            
            current_count = query.scalar() or 0
            usage_percentage = (current_count / rate_limit.max_requests * 100) if rate_limit.max_requests > 0 else 0
            
            if current_count >= rate_limit.max_requests:
                status = "exceeded"
            elif usage_percentage >= 80:
                status = "warning" if status != "exceeded" else status
            
            rate_limit_configs.append({
                "scope": rate_limit.scope.value,
                "max_requests": rate_limit.max_requests,
                "time_window_seconds": rate_limit.time_window_seconds,
                "current_usage": current_count,
                "usage_percentage": round(usage_percentage, 2),
                "remaining": max(0, rate_limit.max_requests - current_count)
            })
            
            current_usage[rate_limit.scope.value] = {
                "current": current_count,
                "max": rate_limit.max_requests,
                "remaining": max(0, rate_limit.max_requests - current_count)
            }
        
        return RateLimitStatusResponse(
            tool_id=tool_id,
            tool_name=tool.name,
            rate_limits=rate_limit_configs,
            current_usage=current_usage,
            status=status
        )
    
    @staticmethod
    def get_agent_stats(
        db: Session,
        agent_id: str
    ) -> Optional[AgentStatsResponse]:
        """Get statistics for a specific agent"""
        # Get execution statistics
        stats = db.query(
            func.count(ToolExecution.id).label('total'),
            func.sum(case((ToolExecution.status == ExecutionStatus.SUCCESS, 1), else_=0)).label('successful'),
            func.sum(case((ToolExecution.status == ExecutionStatus.FAILED, 1), else_=0)).label('failed'),
            func.count(func.distinct(ToolExecution.tool_id)).label('tools_used'),
            func.sum(ToolExecution.cost).label('total_cost'),
            func.max(ToolExecution.created_at).label('last_execution')
        ).filter(
            ToolExecution.agent_id == agent_id
        ).first()
        
        if not stats or stats.total == 0:
            return None
        
        return AgentStatsResponse(
            agent_id=agent_id,
            total_executions=stats.total or 0,
            successful_executions=stats.successful or 0,
            failed_executions=stats.failed or 0,
            tools_used=stats.tools_used or 0,
            total_cost=float(stats.total_cost) if stats.total_cost else None,
            last_execution_at=stats.last_execution
        )
    
    @staticmethod
    def get_role_stats(
        db: Session,
        role_id: UUID
    ) -> Optional[RoleStatsResponse]:
        """Get statistics for a specific role"""
        from app.database.models import Role
        
        role = db.query(Role).filter(Role.id == role_id).first()
        if not role:
            return None
        
        # Get execution statistics
        stats = db.query(
            func.count(ToolExecution.id).label('total'),
            func.sum(case((ToolExecution.status == ExecutionStatus.SUCCESS, 1), else_=0)).label('successful'),
            func.sum(case((ToolExecution.status == ExecutionStatus.FAILED, 1), else_=0)).label('failed'),
            func.count(func.distinct(ToolExecution.tool_id)).label('tools_used'),
            func.sum(ToolExecution.cost).label('total_cost'),
            func.max(ToolExecution.created_at).label('last_execution')
        ).filter(
            ToolExecution.role_id == role_id
        ).first()
        
        if not stats or stats.total == 0:
            return None
        
        return RoleStatsResponse(
            role_id=role_id,
            role_name=role.name,
            total_executions=stats.total or 0,
            successful_executions=stats.successful or 0,
            failed_executions=stats.failed or 0,
            tools_used=stats.tools_used or 0,
            total_cost=float(stats.total_cost) if stats.total_cost else None,
            last_execution_at=stats.last_execution
        )
    
    @staticmethod
    def get_top_tools(
        db: Session,
        limit: int = 10,
        days: Optional[int] = None
    ) -> List[TopToolResponse]:
        """Get top tools by execution count"""
        query = db.query(
            ToolExecution.tool_id,
            func.count(ToolExecution.id).label('execution_count'),
            func.sum(case((ToolExecution.status == ExecutionStatus.SUCCESS, 1), else_=0)).label('successful'),
            func.avg(ToolExecution.execution_time_ms).label('avg_time')
        ).group_by(
            ToolExecution.tool_id
        )
        
        if days:
            start_time = datetime.utcnow() - timedelta(days=days)
            query = query.filter(ToolExecution.created_at >= start_time)
        
        results = query.order_by(
            func.count(ToolExecution.id).desc()
        ).limit(limit).all()
        
        top_tools = []
        for row in results:
            tool = db.query(Tool).filter(Tool.id == row.tool_id).first()
            if not tool:
                continue
            
            total = row.execution_count or 0
            successful = row.successful or 0
            success_rate = (successful / total * 100) if total > 0 else 0.0
            
            top_tools.append(TopToolResponse(
                tool_id=row.tool_id,
                tool_name=tool.name,
                execution_count=total,
                success_rate=round(success_rate, 2),
                average_execution_time_ms=float(row.avg_time) if row.avg_time else None
            ))
        
        return top_tools

