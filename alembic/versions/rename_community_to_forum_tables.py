"""rename_community_to_forum_tables

Revision ID: rename_community_to_forum
Revises: f979d551502a
Create Date: 2024-01-01 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = 'rename_community_to_forum'
down_revision = 'f979d551502a'
branch_labels = None
depends_on = None


def upgrade():
    # Create new forum_questions table
    op.create_table('forum_questions',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('author_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('title', sa.String(length=200), nullable=False),
        sa.Column('content', sa.Text(), nullable=False),
        sa.Column('category', sa.Enum('anxiety', 'depression', 'stress', 'relationships', 'addiction', 'trauma', 'general', 'other', name='questioncategory'), nullable=False),
        sa.Column('tags', sa.String(length=500), nullable=True),
        sa.Column('is_anonymous', sa.Boolean(), nullable=False, default=False),
        sa.Column('status', sa.Enum('open', 'answered', 'closed', name='questionstatus'), nullable=False, default='open'),
        sa.Column('answers_count', sa.Integer(), nullable=False, default=0),
        sa.Column('views_count', sa.Integer(), nullable=False, default=0),
        sa.Column('asked_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('is_active', sa.Boolean(), nullable=False, default=True),
        sa.Column('is_featured', sa.Boolean(), nullable=False, default=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('is_deleted', sa.Boolean(), nullable=False, default=False),
        sa.ForeignKeyConstraint(['author_id'], ['patients.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Create indexes for forum_questions
    op.create_index(op.f('ix_forum_questions_author_id'), 'forum_questions', ['author_id'], unique=False)
    op.create_index(op.f('ix_forum_questions_category'), 'forum_questions', ['category'], unique=False)
    op.create_index(op.f('ix_forum_questions_status'), 'forum_questions', ['status'], unique=False)
    op.create_index(op.f('ix_forum_questions_is_anonymous'), 'forum_questions', ['is_anonymous'], unique=False)
    op.create_index(op.f('ix_forum_questions_answers_count'), 'forum_questions', ['answers_count'], unique=False)
    op.create_index(op.f('ix_forum_questions_views_count'), 'forum_questions', ['views_count'], unique=False)
    op.create_index(op.f('ix_forum_questions_asked_at'), 'forum_questions', ['asked_at'], unique=False)
    op.create_index(op.f('ix_forum_questions_is_active'), 'forum_questions', ['is_active'], unique=False)
    op.create_index(op.f('ix_forum_questions_is_featured'), 'forum_questions', ['is_featured'], unique=False)
    
    # Create forum_answers table
    op.create_table('forum_answers',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('question_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('specialist_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('content', sa.Text(), nullable=False),
        sa.Column('status', sa.Enum('active', 'flagged', 'removed', name='answerstatus'), nullable=False, default='active'),
        sa.Column('answered_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('is_active', sa.Boolean(), nullable=False, default=True),
        sa.Column('is_best_answer', sa.Boolean(), nullable=False, default=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('is_deleted', sa.Boolean(), nullable=False, default=False),
        sa.ForeignKeyConstraint(['question_id'], ['forum_questions.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['specialist_id'], ['specialists.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Create indexes for forum_answers
    op.create_index(op.f('ix_forum_answers_question_id'), 'forum_answers', ['question_id'], unique=False)
    op.create_index(op.f('ix_forum_answers_specialist_id'), 'forum_answers', ['specialist_id'], unique=False)
    op.create_index(op.f('ix_forum_answers_status'), 'forum_answers', ['status'], unique=False)
    op.create_index(op.f('ix_forum_answers_answered_at'), 'forum_answers', ['answered_at'], unique=False)
    op.create_index(op.f('ix_forum_answers_is_active'), 'forum_answers', ['is_active'], unique=False)
    op.create_index(op.f('ix_forum_answers_is_best_answer'), 'forum_answers', ['is_best_answer'], unique=False)
    
    # Drop old community tables
    op.drop_index(op.f('ix_community_post_likes_user_id'), table_name='community_post_likes')
    op.drop_index(op.f('ix_community_post_likes_post_id'), table_name='community_post_likes')
    op.drop_table('community_post_likes')
    op.drop_index(op.f('ix_community_post_comments_post_id'), table_name='community_post_comments')
    op.drop_index(op.f('ix_community_post_comments_is_active'), table_name='community_post_comments')
    op.drop_index(op.f('ix_community_post_comments_commented_at'), table_name='community_post_comments')
    op.drop_index(op.f('ix_community_post_comments_author_id'), table_name='community_post_comments')
    op.drop_table('community_post_comments')
    op.drop_index(op.f('ix_community_posts_posted_at'), table_name='community_posts')
    op.drop_index(op.f('ix_community_posts_likes_count'), table_name='community_posts')
    op.drop_index(op.f('ix_community_posts_is_featured'), table_name='community_posts')
    op.drop_index(op.f('ix_community_posts_is_active'), table_name='community_posts')
    op.drop_index(op.f('ix_community_posts_comments_count'), table_name='community_posts')
    op.drop_index(op.f('ix_community_posts_author_id'), table_name='community_posts')
    op.drop_table('community_posts')


def downgrade():
    # Recreate old community tables
    op.create_table('community_posts',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('author_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('title', sa.String(length=200), nullable=False),
        sa.Column('content', sa.Text(), nullable=False),
        sa.Column('category', sa.String(length=100), nullable=True),
        sa.Column('tags', sa.String(length=500), nullable=True),
        sa.Column('likes_count', sa.Integer(), nullable=False, default=0),
        sa.Column('comments_count', sa.Integer(), nullable=False, default=0),
        sa.Column('posted_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('is_active', sa.Boolean(), nullable=False, default=True),
        sa.Column('is_featured', sa.Boolean(), nullable=False, default=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('is_deleted', sa.Boolean(), nullable=False, default=False),
        sa.ForeignKeyConstraint(['author_id'], ['patients.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Recreate indexes for community_posts
    op.create_index(op.f('ix_community_posts_author_id'), 'community_posts', ['author_id'], unique=False)
    op.create_index(op.f('ix_community_posts_comments_count'), 'community_posts', ['comments_count'], unique=False)
    op.create_index(op.f('ix_community_posts_is_active'), 'community_posts', ['is_active'], unique=False)
    op.create_index(op.f('ix_community_posts_is_featured'), 'community_posts', ['is_featured'], unique=False)
    op.create_index(op.f('ix_community_posts_likes_count'), 'community_posts', ['likes_count'], unique=False)
    op.create_index(op.f('ix_community_posts_posted_at'), 'community_posts', ['posted_at'], unique=False)
    
    # Recreate community_post_comments table
    op.create_table('community_post_comments',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('post_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('author_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('content', sa.Text(), nullable=False),
        sa.Column('commented_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('is_active', sa.Boolean(), nullable=False, default=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('is_deleted', sa.Boolean(), nullable=False, default=False),
        sa.ForeignKeyConstraint(['post_id'], ['community_posts.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['author_id'], ['patients.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Recreate indexes for community_post_comments
    op.create_index(op.f('ix_community_post_comments_author_id'), 'community_post_comments', ['author_id'], unique=False)
    op.create_index(op.f('ix_community_post_comments_commented_at'), 'community_post_comments', ['commented_at'], unique=False)
    op.create_index(op.f('ix_community_post_comments_is_active'), 'community_post_comments', ['is_active'], unique=False)
    op.create_index(op.f('ix_community_post_comments_post_id'), 'community_post_comments', ['post_id'], unique=False)
    
    # Recreate community_post_likes table
    op.create_table('community_post_likes',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('post_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('liked_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('is_deleted', sa.Boolean(), nullable=False, default=False),
        sa.ForeignKeyConstraint(['post_id'], ['community_posts.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['user_id'], ['patients.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('post_id', 'user_id', name='unique_post_like')
    )
    
    # Recreate indexes for community_post_likes
    op.create_index(op.f('ix_community_post_likes_post_id'), 'community_post_likes', ['post_id'], unique=False)
    op.create_index(op.f('ix_community_post_likes_user_id'), 'community_post_likes', ['user_id'], unique=False)
    
    # Drop new forum tables
    op.drop_index(op.f('ix_forum_answers_is_best_answer'), table_name='forum_answers')
    op.drop_index(op.f('ix_forum_answers_is_active'), table_name='forum_answers')
    op.drop_index(op.f('ix_forum_answers_answered_at'), table_name='forum_answers')
    op.drop_index(op.f('ix_forum_answers_status'), table_name='forum_answers')
    op.drop_index(op.f('ix_forum_answers_specialist_id'), table_name='forum_answers')
    op.drop_index(op.f('ix_forum_answers_question_id'), table_name='forum_answers')
    op.drop_table('forum_answers')
    op.drop_index(op.f('ix_forum_questions_is_featured'), table_name='forum_questions')
    op.drop_index(op.f('ix_forum_questions_is_active'), table_name='forum_questions')
    op.drop_index(op.f('ix_forum_questions_asked_at'), table_name='forum_questions')
    op.drop_index(op.f('ix_forum_questions_views_count'), table_name='forum_questions')
    op.drop_index(op.f('ix_forum_questions_answers_count'), table_name='forum_questions')
    op.drop_index(op.f('ix_forum_questions_is_anonymous'), table_name='forum_questions')
    op.drop_index(op.f('ix_forum_questions_status'), table_name='forum_questions')
    op.drop_index(op.f('ix_forum_questions_category'), table_name='forum_questions')
    op.drop_index(op.f('ix_forum_questions_author_id'), table_name='forum_questions')
    op.drop_table('forum_questions')
