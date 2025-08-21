"""Add forum reports table

Revision ID: add_forum_reports_table
Revises: rename_community_to_forum_tables
Create Date: 2025-08-21 13:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = 'add_forum_reports_table'
down_revision = 'rename_community_to_forum'
branch_labels = None
depends_on = None


def upgrade():
    # Create forum_reports table
    op.create_table('forum_reports',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('reporter_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('specialist_reporter_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('post_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('post_type', sa.String(length=20), nullable=False),
        sa.Column('reason', sa.Text(), nullable=True),
        sa.Column('status', sa.String(length=20), nullable=True),
        sa.Column('moderated_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('moderated_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('moderation_notes', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('created_by', sa.String(length=100), nullable=True),
        sa.Column('updated_by', sa.String(length=100), nullable=True),
        sa.Column('is_deleted', sa.Boolean(), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Create indexes
    op.create_index('idx_forum_report_reporter', 'forum_reports', ['reporter_id'])
    op.create_index('idx_forum_report_post', 'forum_reports', ['post_id', 'post_type'])
    op.create_index('idx_forum_report_status', 'forum_reports', ['status'])
    op.create_index('idx_forum_report_created', 'forum_reports', ['created_at'])
    
    # Add foreign key constraints
    op.create_foreign_key('fk_forum_reports_reporter_patient', 'forum_reports', 'patients', ['reporter_id'], ['id'], ondelete='CASCADE')
    op.create_foreign_key('fk_forum_reports_reporter_specialist', 'forum_reports', 'specialists', ['specialist_reporter_id'], ['id'], ondelete='CASCADE')


def downgrade():
    # Drop foreign key constraints
    op.drop_constraint('fk_forum_reports_reporter_specialist', 'forum_reports', type_='foreignkey')
    op.drop_constraint('fk_forum_reports_reporter_patient', 'forum_reports', type_='foreignkey')
    
    # Drop indexes
    op.drop_index('idx_forum_report_created', table_name='forum_reports')
    op.drop_index('idx_forum_report_status', table_name='forum_reports')
    op.drop_index('idx_forum_report_post', table_name='forum_reports')
    op.drop_index('idx_forum_report_reporter', table_name='forum_reports')
    
    # Drop table
    op.drop_table('forum_reports')
