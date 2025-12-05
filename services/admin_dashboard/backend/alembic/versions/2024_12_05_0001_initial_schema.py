"""Initial database schema for Nexus Admin Dashboard

Revision ID: 0001
Revises: 
Create Date: 2024-12-05
"""

from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = '0001'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Create initial database schema."""
    
    # Create roles table
    op.create_table(
        'roles',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('name', sa.String(100), unique=True, nullable=False),
        sa.Column('description', sa.Text, nullable=True),
        sa.Column('permissions', sa.JSON, nullable=True),
        sa.Column('parent_role_id', sa.String(36), sa.ForeignKey('roles.id', ondelete='SET NULL'), nullable=True),
        sa.Column('is_system_role', sa.Boolean, default=False, nullable=False),
        sa.Column('created_by', sa.String(36), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now(), nullable=False),
        sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index('ix_roles_name', 'roles', ['name'])
    
    # Create users table
    op.create_table(
        'users',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('email', sa.String(255), unique=True, nullable=False),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('password_hash', sa.String(255), nullable=True),
        sa.Column('sso_provider', sa.String(50), default='local', nullable=False),
        sa.Column('sso_id', sa.String(255), nullable=True),
        sa.Column('status', sa.String(20), default='active', nullable=False),
        sa.Column('avatar_url', sa.String(500), nullable=True),
        sa.Column('department', sa.String(100), nullable=True),
        sa.Column('title', sa.String(100), nullable=True),
        sa.Column('last_login', sa.DateTime(timezone=True), nullable=True),
        sa.Column('failed_login_attempts', sa.Integer, default=0, nullable=False),
        sa.Column('locked_until', sa.DateTime(timezone=True), nullable=True),
        sa.Column('password_changed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('metadata', sa.JSON, nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now(), nullable=False),
        sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index('ix_users_email', 'users', ['email'])
    op.create_index('ix_users_status', 'users', ['status'])
    
    # Create user_roles association table
    op.create_table(
        'user_roles',
        sa.Column('user_id', sa.String(36), sa.ForeignKey('users.id', ondelete='CASCADE'), primary_key=True),
        sa.Column('role_id', sa.String(36), sa.ForeignKey('roles.id', ondelete='CASCADE'), primary_key=True),
        sa.Column('assigned_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('assigned_by', sa.String(36), nullable=True),
    )
    
    # Create audit_logs table
    op.create_table(
        'audit_logs',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('timestamp', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column('user_id', sa.String(36), sa.ForeignKey('users.id', ondelete='SET NULL'), nullable=True),
        sa.Column('user_email', sa.String(255), nullable=True),
        sa.Column('action', sa.String(50), nullable=False),
        sa.Column('resource_type', sa.String(50), nullable=False),
        sa.Column('resource_id', sa.String(36), nullable=True),
        sa.Column('details', sa.JSON, nullable=True),
        sa.Column('ip_address', sa.String(45), nullable=True),
        sa.Column('user_agent', sa.String(500), nullable=True),
        sa.Column('success', sa.Boolean, default=True, nullable=False),
        sa.Column('error_message', sa.Text, nullable=True),
    )
    op.create_index('ix_audit_logs_timestamp', 'audit_logs', ['timestamp'])
    op.create_index('ix_audit_logs_user_id', 'audit_logs', ['user_id'])
    op.create_index('ix_audit_logs_action', 'audit_logs', ['action'])
    op.create_index('ix_audit_logs_resource_type', 'audit_logs', ['resource_type'])
    op.create_index('ix_audit_logs_resource_id', 'audit_logs', ['resource_id'])
    op.create_index('ix_audit_user_time', 'audit_logs', ['user_id', 'timestamp'])
    op.create_index('ix_audit_resource', 'audit_logs', ['resource_type', 'resource_id'])
    op.create_index('ix_audit_action_time', 'audit_logs', ['action', 'timestamp'])
    
    # Create refresh_tokens table
    op.create_table(
        'refresh_tokens',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('token_hash', sa.String(128), unique=True, nullable=False),
        sa.Column('user_id', sa.String(36), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column('expires_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('revoked_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('revoked_reason', sa.String(100), nullable=True),
        sa.Column('previous_token_id', sa.String(36), nullable=True),
        sa.Column('device_info', sa.String(500), nullable=True),
        sa.Column('ip_address', sa.String(45), nullable=True),
    )
    op.create_index('ix_refresh_tokens_token_hash', 'refresh_tokens', ['token_hash'])
    op.create_index('ix_refresh_tokens_user_id', 'refresh_tokens', ['user_id'])
    op.create_index('ix_refresh_user_valid', 'refresh_tokens', ['user_id', 'revoked_at', 'expires_at'])
    
    # Insert default system roles
    op.execute("""
        INSERT INTO roles (id, name, description, permissions, is_system_role, created_by, created_at, updated_at)
        VALUES 
        ('admin', 'Admin', 'Full system administrator with all permissions', 
         '["system:admin", "system:config", "system:audit", "users:create", "users:read", "users:update", "users:delete", "roles:create", "roles:read", "roles:update", "roles:delete", "releases:create", "releases:read", "releases:update", "releases:delete", "feature_requests:create", "feature_requests:read", "feature_requests:update", "feature_requests:delete", "health:read", "metrics:read", "audit:read"]',
         true, 'system', NOW(), NOW()),
        ('developer', 'Developer', 'Developer role with release and feature request access',
         '["releases:create", "releases:read", "releases:update", "feature_requests:create", "feature_requests:read", "feature_requests:update", "health:read", "metrics:read"]',
         true, 'system', NOW(), NOW()),
        ('viewer', 'Viewer', 'Read-only access to dashboard data',
         '["releases:read", "feature_requests:read", "health:read", "metrics:read"]',
         true, 'system', NOW(), NOW()),
        ('operator', 'Operator', 'Operations team with health and metrics focus',
         '["releases:read", "health:read", "metrics:read", "system:config"]',
         true, 'system', NOW(), NOW())
    """)
    
    # Insert default admin user
    op.execute("""
        INSERT INTO users (id, email, name, sso_provider, status, created_at, updated_at)
        VALUES ('admin-001', 'admin@nexus.dev', 'System Administrator', 'local', 'active', NOW(), NOW())
    """)
    
    # Assign admin role to admin user
    op.execute("""
        INSERT INTO user_roles (user_id, role_id, assigned_at)
        VALUES ('admin-001', 'admin', NOW())
    """)


def downgrade() -> None:
    """Drop all tables."""
    op.drop_table('refresh_tokens')
    op.drop_table('audit_logs')
    op.drop_table('user_roles')
    op.drop_table('users')
    op.drop_table('roles')

