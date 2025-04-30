"""Initial database migration

Revision ID: 1a19ac33a82c
Revises: 
Create Date: 2023-11-15 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import sqlite
import json

# revision identifiers, used by Alembic.
revision: str = '1a19ac33a82c'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create agents table
    op.create_table(
        'agents',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('description', sa.Text, nullable=True),
        sa.Column('model', sa.String(255), nullable=True),
        sa.Column('workspace_dir', sa.String(512), nullable=False),
        sa.Column('status', sa.String(50), nullable=False, default='idle'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now()),
        sa.Column('config', sqlite.JSON, nullable=True),
        sa.Column('max_iterations', sa.Integer, default=10),
        sa.Column('temperature', sa.Float, default=0.7),
        sa.Column('active', sa.Boolean, default=True),
    )
    
    # Create tasks table
    op.create_table(
        'tasks',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('agent_id', sa.String(36), sa.ForeignKey('agents.id', ondelete='CASCADE'), nullable=False),
        sa.Column('goal', sa.Text, nullable=False),
        sa.Column('status', sa.String(50), nullable=False, default='pending'),
        sa.Column('priority', sa.Integer, default=1),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now()),
        sa.Column('started_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('completed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('plan', sqlite.JSON, nullable=True),
        sa.Column('results', sqlite.JSON, nullable=True),
        sa.Column('reflection', sqlite.JSON, nullable=True),
        sa.Column('error', sa.Text, nullable=True),
        sa.Column('meta_data', sqlite.JSON, nullable=True),
        sa.Column('scheduled_for', sa.DateTime(timezone=True), nullable=True),
    )
    
    # Create task steps table
    op.create_table(
        'task_steps',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('task_id', sa.String(36), sa.ForeignKey('tasks.id', ondelete='CASCADE'), nullable=False),
        sa.Column('step_number', sa.Integer, nullable=False),
        sa.Column('action', sa.Text, nullable=False),
        sa.Column('tool', sa.String(255), nullable=True),
        sa.Column('input_data', sqlite.JSON, nullable=True),
        sa.Column('output_data', sqlite.JSON, nullable=True),
        sa.Column('status', sa.String(50), nullable=False, default='pending'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now()),
        sa.Column('started_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('completed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('error', sa.Text, nullable=True),
    )
    
    # Create users table
    op.create_table(
        'users',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('username', sa.String(255), unique=True, nullable=False),
        sa.Column('email', sa.String(255), unique=True, nullable=False),
        sa.Column('hashed_password', sa.String(255), nullable=False),
        sa.Column('full_name', sa.String(255), nullable=True),
        sa.Column('is_active', sa.Boolean, default=True),
        sa.Column('is_superuser', sa.Boolean, default=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now()),
        sa.Column('last_login', sa.DateTime(timezone=True), nullable=True),
        sa.Column('api_key', sa.String(255), unique=True, nullable=True),
    )
    
    # Create tool executions table
    op.create_table(
        'tool_executions',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('task_step_id', sa.String(36), sa.ForeignKey('task_steps.id', ondelete='CASCADE'), nullable=False),
        sa.Column('tool_name', sa.String(255), nullable=False),
        sa.Column('inputs', sqlite.JSON, nullable=True),
        sa.Column('outputs', sqlite.JSON, nullable=True),
        sa.Column('duration_ms', sa.Integer, nullable=True),
        sa.Column('status', sa.String(50), nullable=False, default='success'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('error', sa.Text, nullable=True),
    )
    
    # Create indexes
    op.create_index('idx_agent_name', 'agents', ['name'])
    op.create_index('idx_agent_status', 'agents', ['status'])
    op.create_index('idx_agent_active', 'agents', ['active'])
    
    op.create_index('idx_task_agent_id', 'tasks', ['agent_id'])
    op.create_index('idx_task_status', 'tasks', ['status'])
    op.create_index('idx_task_priority', 'tasks', ['priority'])
    op.create_index('idx_task_scheduled_for', 'tasks', ['scheduled_for'])
    
    op.create_index('idx_step_task_id', 'task_steps', ['task_id'])
    op.create_index('idx_step_number', 'task_steps', ['step_number'])
    op.create_index('idx_step_status', 'task_steps', ['status'])
    
    op.create_index('idx_user_is_active', 'users', ['is_active'])
    
    op.create_index('idx_tool_execution_task_step', 'tool_executions', ['task_step_id'])
    op.create_index('idx_tool_execution_tool_name', 'tool_executions', ['tool_name'])


def downgrade() -> None:
    # Drop tables in reverse order
    op.drop_table('tool_executions')
    op.drop_table('task_steps')
    op.drop_table('tasks')
    op.drop_table('users')
    op.drop_table('agents') 