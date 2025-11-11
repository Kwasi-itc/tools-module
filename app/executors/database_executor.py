from sqlalchemy import create_engine, text
from sqlalchemy.orm import Session
from typing import Dict, Any, Optional, List
import json
from app.database.models import Tool, ToolConfig


class DatabaseExecutor:
    """Executor for database query tools"""
    
    @staticmethod
    def execute(
        tool: Tool,
        input_data: Dict[str, Any],
        db_session: Optional[Session] = None,
        timeout: int = 30
    ) -> Dict[str, Any]:
        """
        Execute a database query tool.
        
        Args:
            tool: Tool model instance
            input_data: Input parameters for the query
            db_session: Optional existing database session
            timeout: Query timeout in seconds
            
        Returns:
            Dict containing query results
        """
        # Get tool configurations
        configs = {config.config_key: config.config_value for config in tool.configs}
        
        connection_string = configs.get("connection_string")
        if not connection_string:
            raise ValueError("Database connection_string not configured for this tool")
        
        query_template = configs.get("query_template")
        if not query_template:
            raise ValueError("Query template not configured for this tool")
        
        # Create engine if no session provided
        if db_session is None:
            engine = create_engine(
                connection_string,
                pool_pre_ping=True,
                connect_args={"connect_timeout": timeout}
            )
            use_external_engine = True
        else:
            engine = db_session.bind
            use_external_engine = False
        
        try:
            # Replace parameters in query template
            # Support both :param and {param} syntax
            query = query_template
            if ":" in query:
                # SQLAlchemy parameterized query
                query = text(query)
                params = input_data
            else:
                # Simple string replacement (less safe, but flexible)
                query = query.format(**input_data)
                params = {}
            
            # Execute query
            with engine.connect() as conn:
                if isinstance(query, str):
                    result = conn.execute(text(query), params)
                else:
                    result = conn.execute(query, params)
                
                # Fetch results
                if result.returns_rows:
                    rows = result.fetchall()
                    columns = result.keys()
                    
                    # Convert to list of dicts
                    results = [dict(zip(columns, row)) for row in rows]
                    
                    return {
                        "row_count": len(results),
                        "data": results
                    }
                else:
                    # For INSERT/UPDATE/DELETE
                    return {
                        "row_count": result.rowcount,
                        "message": "Query executed successfully"
                    }
        
        except Exception as e:
            raise Exception(f"Database query failed: {str(e)}")
        finally:
            if use_external_engine:
                engine.dispose()

