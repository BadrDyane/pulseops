"""initial_schema

Revision ID: a8b4e3986c0a
Revises: 
Create Date: 2026-06-04

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = 'a8b4e3986c0a'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ------------------------------------------------------------------ #
    # projects
    # ------------------------------------------------------------------ #
    op.create_table(
        'projects',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('name', sa.String(), nullable=False),
        sa.Column('slug', sa.String(), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('slug'),
    )

    # ------------------------------------------------------------------ #
    # api_keys
    # ------------------------------------------------------------------ #
    op.create_table(
        'api_keys',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('project_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('key_prefix', sa.String(length=20), nullable=False),
        sa.Column('key_hash', sa.String(length=64), nullable=False),
        sa.Column('label', sa.String(), nullable=True),
        sa.Column('last_used_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=False),
        sa.Column('expires_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['project_id'], ['projects.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('key_hash'),
    )
    op.create_index('idx_api_keys_project_id', 'api_keys', ['project_id'])
    op.create_index('idx_api_keys_key_hash', 'api_keys', ['key_hash'])

    # ------------------------------------------------------------------ #
    # prompt_versions
    # ------------------------------------------------------------------ #
    op.create_table(
        'prompt_versions',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('project_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('feature', sa.String(), nullable=False),
        sa.Column('version_hash', sa.String(length=64), nullable=False),
        sa.Column('version_num', sa.Integer(), nullable=False),
        sa.Column('system_msg', sa.Text(), nullable=True),
        sa.Column('user_template', sa.Text(), nullable=True),
        sa.Column('model', sa.String(), nullable=False),
        sa.ForeignKeyConstraint(['project_id'], ['projects.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('project_id', 'feature', 'version_hash'),
    )
    op.create_index('idx_pv_project_feature', 'prompt_versions', ['project_id', 'feature'])
    op.create_index('idx_pv_hash', 'prompt_versions', ['project_id', 'version_hash'])

    # ------------------------------------------------------------------ #
    # llm_events  (plain table — no partitioning in v1 local dev)
    # ------------------------------------------------------------------ #
    op.create_table(
        'llm_events',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('project_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('model', sa.String(), nullable=False),
        sa.Column('feature', sa.String(), nullable=True),
        sa.Column('tenant_id', sa.String(), nullable=True),
        sa.Column('user_id', sa.String(), nullable=True),
        sa.Column('tags', postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column('messages_json', sa.Text(), nullable=True),
        sa.Column('response_text', sa.Text(), nullable=True),
        sa.Column('is_truncated', sa.Boolean(), nullable=False),
        sa.Column('latency_ms', sa.Integer(), nullable=False),
        sa.Column('input_tokens', sa.Integer(), nullable=False),
        sa.Column('output_tokens', sa.Integer(), nullable=False),
        sa.Column('total_tokens', sa.Integer(), nullable=False),
        sa.Column('cost_usd', sa.Numeric(precision=12, scale=8), nullable=False),
        sa.Column('is_error', sa.Boolean(), nullable=False),
        sa.Column('error_code', sa.String(), nullable=True),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('prompt_version_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('parent_event_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('sample_rate', sa.Numeric(precision=4, scale=3), nullable=False),
        sa.ForeignKeyConstraint(['project_id'], ['projects.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('idx_le_project_time', 'llm_events', ['project_id', sa.text('created_at DESC')])
    op.create_index('idx_le_project_feature', 'llm_events', ['project_id', 'feature', sa.text('created_at DESC')])
    op.create_index('idx_le_project_model', 'llm_events', ['project_id', 'model', sa.text('created_at DESC')])
    op.create_index('idx_le_tenant', 'llm_events', ['project_id', 'tenant_id', sa.text('created_at DESC')],
                    postgresql_where=sa.text('tenant_id IS NOT NULL'))
    op.create_index('idx_le_errors', 'llm_events', ['project_id', sa.text('created_at DESC')],
                    postgresql_where=sa.text('is_error = TRUE'))
    op.create_index('idx_le_parent', 'llm_events', ['parent_event_id'],
                    postgresql_where=sa.text('parent_event_id IS NOT NULL'))
    # Idempotency index on client_event_id stored in tags
    op.execute("""
        CREATE UNIQUE INDEX idx_le_client_id
        ON llm_events ((tags->>'_client_event_id'))
        WHERE tags->>'_client_event_id' IS NOT NULL
    """)

    # ------------------------------------------------------------------ #
    # hourly_rollups
    # ------------------------------------------------------------------ #
    op.create_table(
        'hourly_rollups',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('project_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('hour_bucket', sa.DateTime(timezone=True), nullable=False),
        sa.Column('feature', sa.String(), nullable=True),
        sa.Column('model', sa.String(), nullable=True),
        sa.Column('request_count', sa.Integer(), nullable=False),
        sa.Column('error_count', sa.Integer(), nullable=False),
        sa.Column('total_tokens', sa.BigInteger(), nullable=False),
        sa.Column('total_cost_usd', sa.Numeric(precision=14, scale=8), nullable=False),
        sa.Column('sum_latency_ms', sa.BigInteger(), nullable=False),
        sa.Column('p50_latency_ms', sa.Integer(), nullable=True),
        sa.Column('p95_latency_ms', sa.Integer(), nullable=True),
        sa.Column('p99_latency_ms', sa.Integer(), nullable=True),
        sa.ForeignKeyConstraint(['project_id'], ['projects.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('project_id', 'hour_bucket', 'feature', 'model'),
    )
    op.create_index('idx_hr_project_hour', 'hourly_rollups', ['project_id', sa.text('hour_bucket DESC')])
    op.create_index('idx_hr_feature', 'hourly_rollups', ['project_id', 'feature', sa.text('hour_bucket DESC')],
                    postgresql_where=sa.text('feature IS NOT NULL'))

    # ------------------------------------------------------------------ #
    # eval_definitions
    # ------------------------------------------------------------------ #
    op.create_table(
        'eval_definitions',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('project_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('feature', sa.String(), nullable=False),
        sa.Column('name', sa.String(), nullable=False),
        sa.Column('eval_type', sa.String(), nullable=False),
        sa.Column('config', postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column('is_active', sa.Boolean(), nullable=False),
        sa.ForeignKeyConstraint(['project_id'], ['projects.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('project_id', 'feature', 'name'),
    )
    op.create_index('idx_ed_project_feature', 'eval_definitions', ['project_id', 'feature'],
                    postgresql_where=sa.text('is_active = TRUE'))

    # ------------------------------------------------------------------ #
    # eval_queue
    # ------------------------------------------------------------------ #
    op.create_table(
        'eval_queue',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('event_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('project_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('feature', sa.String(), nullable=True),
        sa.Column('status', sa.String(), nullable=False),
        sa.Column('attempts', sa.Integer(), nullable=False),
        sa.Column('locked_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('error', sa.Text(), nullable=True),
        sa.ForeignKeyConstraint(['project_id'], ['projects.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('idx_eq_pending', 'eval_queue', [sa.text('created_at ASC')],
                    postgresql_where=sa.text("status = 'pending'"))
    op.create_index('idx_eq_project', 'eval_queue', ['project_id', sa.text('created_at DESC')])

    # ------------------------------------------------------------------ #
    # eval_results
    # ------------------------------------------------------------------ #
    op.create_table(
        'eval_results',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('event_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('project_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('eval_def_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('feature', sa.String(), nullable=False),
        sa.Column('prompt_version_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('passed', sa.Boolean(), nullable=False),
        sa.Column('score', sa.Numeric(precision=4, scale=2), nullable=True),
        sa.Column('rationale', sa.Text(), nullable=True),
        sa.Column('error', sa.Text(), nullable=True),
        sa.ForeignKeyConstraint(['eval_def_id'], ['eval_definitions.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['project_id'], ['projects.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('idx_er_project_feature', 'eval_results', ['project_id', 'feature', sa.text('created_at DESC')])
    op.create_index('idx_er_eval_def', 'eval_results', ['eval_def_id', sa.text('created_at DESC')])
    op.create_index('idx_er_event', 'eval_results', ['event_id'])

    # ------------------------------------------------------------------ #
    # replay_events
    # ------------------------------------------------------------------ #
    op.create_table(
        'replay_events',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('project_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('original_event_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('replayed_event_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('target_model', sa.String(), nullable=False),
        sa.Column('status', sa.String(), nullable=False),
        sa.Column('cost_diff_usd', sa.Numeric(precision=12, scale=8), nullable=True),
        sa.Column('latency_diff_ms', sa.Integer(), nullable=True),
        sa.Column('error', sa.Text(), nullable=True),
        sa.ForeignKeyConstraint(['project_id'], ['projects.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('idx_re_project', 'replay_events', ['project_id', sa.text('created_at DESC')])
    op.create_index('idx_re_original', 'replay_events', ['original_event_id'])

    # ------------------------------------------------------------------ #
    # alert_rules
    # ------------------------------------------------------------------ #
    op.create_table(
        'alert_rules',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('project_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('name', sa.String(), nullable=False),
        sa.Column('rule_type', sa.String(), nullable=False),
        sa.Column('scope', postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column('config', postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column('webhook_url', sa.Text(), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=False),
        sa.ForeignKeyConstraint(['project_id'], ['projects.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('project_id', 'name'),
    )
    op.create_index('idx_ar_project', 'alert_rules', ['project_id'],
                    postgresql_where=sa.text('is_active = TRUE'))

    # ------------------------------------------------------------------ #
    # alerts_fired
    # ------------------------------------------------------------------ #
    op.create_table(
        'alerts_fired',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('rule_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('project_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('triggered_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('payload', postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column('webhook_status', sa.Integer(), nullable=True),
        sa.ForeignKeyConstraint(['project_id'], ['projects.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['rule_id'], ['alert_rules.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('idx_af_rule', 'alerts_fired', ['rule_id', sa.text('triggered_at DESC')])
    op.create_index('idx_af_project', 'alerts_fired', ['project_id', sa.text('triggered_at DESC')])

    # ------------------------------------------------------------------ #
    # drift_snapshots
    # ------------------------------------------------------------------ #
    op.create_table(
        'drift_snapshots',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('project_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('feature', sa.String(), nullable=False),
        sa.Column('window_start', sa.DateTime(timezone=True), nullable=False),
        sa.Column('window_end', sa.DateTime(timezone=True), nullable=False),
        sa.Column('sample_count', sa.Integer(), nullable=False),
        sa.Column('avg_response_len', sa.Numeric(precision=10, scale=2), nullable=True),
        sa.Column('avg_output_tokens', sa.Numeric(precision=10, scale=2), nullable=True),
        sa.Column('p50_output_tokens', sa.Integer(), nullable=True),
        sa.Column('p95_output_tokens', sa.Integer(), nullable=True),
        sa.Column('avg_latency_ms', sa.Numeric(precision=10, scale=2), nullable=True),
        sa.Column('frac_json', sa.Numeric(precision=5, scale=4), nullable=True),
        sa.Column('frac_error', sa.Numeric(precision=5, scale=4), nullable=True),
        sa.Column('is_drifted', sa.Boolean(), nullable=False),
        sa.Column('drift_metrics', postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.ForeignKeyConstraint(['project_id'], ['projects.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('idx_ds_project_feature', 'drift_snapshots', ['project_id', 'feature', sa.text('created_at DESC')])


def downgrade() -> None:
    op.drop_table('drift_snapshots')
    op.drop_table('alerts_fired')
    op.drop_table('alert_rules')
    op.drop_table('replay_events')
    op.drop_table('eval_results')
    op.drop_table('eval_queue')
    op.drop_table('eval_definitions')
    op.drop_table('hourly_rollups')
    op.drop_table('llm_events')
    op.drop_table('prompt_versions')
    op.drop_table('api_keys')
    op.drop_table('projects')