"""Initial migration - create all tables

Revision ID: 001_initial
Revises: 
Create Date: 2024-01-01 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '001_initial'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Define enum types. They will be created when referenced in table definitions.
    tool_type_enum = postgresql.ENUM('http', 'database', name='tooltype', create_type=True)
    execution_status_enum = postgresql.ENUM('pending', 'running', 'success', 'failed', name='executionstatus', create_type=True)
    rate_limit_scope_enum = postgresql.ENUM('global', 'user', 'agent', name='ratelimitscope', create_type=True)
    permission_action_enum = postgresql.ENUM('read', 'execute', 'manage', name='permissionaction', create_type=True)
    parameter_type_enum = postgresql.ENUM('input', 'output', name='parametertype', create_type=True)
    
    # Create roles table first (no dependencies)
    op.create_table(
        'roles',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('name', sa.String(255), nullable=False, unique=True),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text("timezone('utc', now())")),
    )
    op.create_index('ix_roles_name', 'roles', ['name'])
    
    # Create tools table
    op.create_table(
        'tools',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('name', sa.String(255), nullable=False, unique=True),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('type', tool_type_enum, nullable=False),
        sa.Column('version', sa.String(50), nullable=False, server_default='1.0.0'),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('tool_metadata', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text("timezone('utc', now())")),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.text("timezone('utc', now())"), server_onupdate=sa.text("timezone('utc', now())")),
    )
    op.create_index('ix_tools_name', 'tools', ['name'])
    
    # Create tool_parameters table
    op.create_table(
        'tool_parameters',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('tool_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('type', sa.String(50), nullable=False),
        sa.Column('required', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('default_value', sa.Text(), nullable=True),
        sa.Column('parameter_type', parameter_type_enum, nullable=False),
        sa.ForeignKeyConstraint(['tool_id'], ['tools.id'], ondelete='CASCADE'),
    )
    op.create_index('ix_tool_parameters_tool_id', 'tool_parameters', ['tool_id'])
    
    # Create tool_configs table
    op.create_table(
        'tool_configs',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('tool_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('config_key', sa.String(255), nullable=False),
        sa.Column('config_value', sa.Text(), nullable=True),
        sa.ForeignKeyConstraint(['tool_id'], ['tools.id'], ondelete='CASCADE'),
        sa.UniqueConstraint('tool_id', 'config_key', name='uq_tool_config'),
    )
    op.create_index('ix_tool_configs_tool_id', 'tool_configs', ['tool_id'])
    
    # Create tool_rate_limits table
    op.create_table(
        'tool_rate_limits',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('tool_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('max_requests', sa.Integer(), nullable=False),
        sa.Column('time_window_seconds', sa.Integer(), nullable=False),
        sa.Column('scope', rate_limit_scope_enum, nullable=False, server_default='global'),
        sa.ForeignKeyConstraint(['tool_id'], ['tools.id'], ondelete='CASCADE'),
    )
    op.create_index('ix_tool_rate_limits_tool_id', 'tool_rate_limits', ['tool_id'])
    
    # Create tool_executions table
    op.create_table(
        'tool_executions',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('tool_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('agent_id', sa.String(255), nullable=False),
        sa.Column('role_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('status', execution_status_enum, nullable=False, server_default='pending'),
        sa.Column('input_data', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('output_data', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('execution_time_ms', sa.Integer(), nullable=True),
        sa.Column('cost', sa.Numeric(10, 4), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text("timezone('utc', now())")),
        sa.ForeignKeyConstraint(['tool_id'], ['tools.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['role_id'], ['roles.id'], ondelete='SET NULL'),
    )
    op.create_index('ix_tool_executions_tool_id', 'tool_executions', ['tool_id'])
    op.create_index('ix_tool_executions_agent_id', 'tool_executions', ['agent_id'])
    op.create_index('ix_tool_executions_role_id', 'tool_executions', ['role_id'])
    op.create_index('ix_tool_executions_created_at', 'tool_executions', ['created_at'])
    
    # Create tool_permissions table
    op.create_table(
        'tool_permissions',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('tool_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('role_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('action', permission_action_enum, nullable=False),
        sa.Column('granted', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text("timezone('utc', now())")),
        sa.ForeignKeyConstraint(['tool_id'], ['tools.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['role_id'], ['roles.id'], ondelete='CASCADE'),
        sa.UniqueConstraint('tool_id', 'role_id', 'action', name='uq_tool_permission'),
    )
    op.create_index('ix_tool_permissions_tool_id', 'tool_permissions', ['tool_id'])
    op.create_index('ix_tool_permissions_role_id', 'tool_permissions', ['role_id'])


def downgrade() -> None:
    # Drop tables in reverse order
    op.drop_table('tool_permissions')
    op.drop_table('tool_executions')
    op.drop_table('tool_rate_limits')
    op.drop_table('tool_configs')
    op.drop_table('tool_parameters')
    op.drop_table('tools')
    op.drop_table('roles')
    
    # Drop enum types
    op.execute('DROP TYPE IF EXISTS permissionaction')
    op.execute('DROP TYPE IF EXISTS parametertype')
    op.execute('DROP TYPE IF EXISTS ratelimitscope')
    op.execute('DROP TYPE IF EXISTS executionstatus')
    op.execute('DROP TYPE IF EXISTS tooltype')

