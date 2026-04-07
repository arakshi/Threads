"""init

Revision ID: 20260407_0001
Revises:
Create Date: 2026-04-07
"""

from alembic import op
import sqlalchemy as sa

revision = '20260407_0001'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table('accounts', sa.Column('id', sa.Integer(), primary_key=True), sa.Column('handle', sa.String(120), nullable=False), sa.Column('display_name', sa.String(255)), sa.Column('profile_url', sa.String(500)), sa.Column('followers_hint', sa.Integer()), sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP')))
    op.create_index('ix_accounts_handle', 'accounts', ['handle'], unique=True)
    op.create_table('topics', sa.Column('id', sa.Integer(), primary_key=True), sa.Column('name', sa.String(120), nullable=False), sa.Column('keywords_csv', sa.Text(), nullable=False, server_default=''), sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP')))
    op.create_table('posts', sa.Column('id', sa.Integer(), primary_key=True), sa.Column('external_id', sa.String(255), nullable=False), sa.Column('source', sa.String(64), nullable=False), sa.Column('account_id', sa.Integer(), sa.ForeignKey('accounts.id')), sa.Column('post_url', sa.String(1000), nullable=False), sa.Column('text', sa.Text()), sa.Column('created_at_external', sa.DateTime(timezone=True)), sa.Column('likes', sa.Integer()), sa.Column('replies', sa.Integer()), sa.Column('reposts', sa.Integer()), sa.Column('quotes', sa.Integer()), sa.Column('has_media', sa.Boolean(), nullable=False, server_default='0'), sa.Column('media_count', sa.Integer(), nullable=False, server_default='0'), sa.Column('language', sa.String(10)), sa.Column('viral_score', sa.Float()), sa.Column('engagement_rate', sa.Float()), sa.Column('sentiment', sa.String(20)), sa.Column('tone', sa.String(40)), sa.Column('format_type', sa.String(40)), sa.Column('hook', sa.String(255)), sa.Column('cta', sa.String(255)), sa.Column('dedup_hash', sa.String(64)), sa.Column('cluster_id', sa.Integer()), sa.Column('collected_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP')), sa.UniqueConstraint('external_id', name='uq_posts_external_id'), sa.UniqueConstraint('post_url')))
    op.create_index('ix_posts_external_id', 'posts', ['external_id'])
    op.create_index('ix_posts_dedup_hash', 'posts', ['dedup_hash'])
    op.create_table('pattern_insights', sa.Column('id', sa.Integer(), primary_key=True), sa.Column('topic', sa.String(120), nullable=False), sa.Column('pattern_type', sa.String(60), nullable=False), sa.Column('value', sa.Text(), nullable=False), sa.Column('score', sa.Float()), sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP')))
    op.create_table('job_runs', sa.Column('id', sa.Integer(), primary_key=True), sa.Column('job_name', sa.String(100), nullable=False), sa.Column('status', sa.String(30), nullable=False), sa.Column('details', sa.Text()), sa.Column('started_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP')), sa.Column('finished_at', sa.DateTime(timezone=True)))


def downgrade() -> None:
    op.drop_table('job_runs')
    op.drop_table('pattern_insights')
    op.drop_index('ix_posts_dedup_hash', table_name='posts')
    op.drop_index('ix_posts_external_id', table_name='posts')
    op.drop_table('posts')
    op.drop_table('topics')
    op.drop_index('ix_accounts_handle', table_name='accounts')
    op.drop_table('accounts')
