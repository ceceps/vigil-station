"""Initial database schema

Revision ID: 001
Revises: 
Create Date: 2026-08-10 03:09:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '001'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create tle_cache table
    op.create_table(
        'tle_cache',
        sa.Column('norad_id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('tle_line1', sa.String(length=255), nullable=False),
        sa.Column('tle_line2', sa.String(length=255), nullable=False),
        sa.Column('satellite_group', sa.String(length=100), nullable=False),
        sa.Column('fetched_at', sa.DateTime(), nullable=False),
        sa.Column('extra_data', sa.Text(), nullable=True),
        sa.PrimaryKeyConstraint('norad_id')
    )
    op.create_index(op.f('ix_tle_cache_norad_id'), 'tle_cache', ['norad_id'], unique=False)
    op.create_index(op.f('ix_tle_cache_satellite_group'), 'tle_cache', ['satellite_group'], unique=False)

    # Create schedules table
    op.create_table(
        'schedules',
        sa.Column('id', sa.String(length=255), nullable=False),
        sa.Column('satellite_id', sa.Integer(), nullable=False),
        sa.Column('ground_station_id', sa.Integer(), nullable=False),
        sa.Column('start_time', sa.DateTime(), nullable=False),
        sa.Column('end_time', sa.DateTime(), nullable=False),
        sa.Column('max_elevation_deg', sa.Float(), nullable=False),
        sa.Column('status', sa.String(length=50), nullable=False),
        sa.Column('approved', sa.Boolean(), nullable=True),
        sa.Column('override_reason', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_schedules_satellite_id'), 'schedules', ['satellite_id'], unique=False)
    op.create_index(op.f('ix_schedules_ground_station_id'), 'schedules', ['ground_station_id'], unique=False)

    # Create conflicts table
    op.create_table(
        'conflicts',
        sa.Column('id', sa.String(length=255), nullable=False),
        sa.Column('ground_station_id', sa.Integer(), nullable=False),
        sa.Column('pass_ids', sa.Text(), nullable=False),
        sa.Column('overlap_start', sa.DateTime(), nullable=False),
        sa.Column('overlap_end', sa.DateTime(), nullable=False),
        sa.Column('resolved', sa.Boolean(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_conflicts_ground_station_id'), 'conflicts', ['ground_station_id'], unique=False)

    # Create recommendations table
    op.create_table(
        'recommendations',
        sa.Column('id', sa.String(length=255), nullable=False),
        sa.Column('conflict_id', sa.String(length=255), nullable=False),
        sa.Column('suggested_action', sa.String(length=100), nullable=False),
        sa.Column('target_pass_id', sa.String(length=255), nullable=True),
        sa.Column('alternative_window', sa.Text(), nullable=True),
        sa.Column('reasoning', sa.Text(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_recommendations_conflict_id'), 'recommendations', ['conflict_id'], unique=False)


def downgrade() -> None:
    op.drop_index(op.f('ix_recommendations_conflict_id'), table_name='recommendations')
    op.drop_table('recommendations')
    op.drop_index(op.f('ix_conflicts_ground_station_id'), table_name='conflicts')
    op.drop_table('conflicts')
    op.drop_index(op.f('ix_schedules_ground_station_id'), table_name='schedules')
    op.drop_index(op.f('ix_schedules_satellite_id'), table_name='schedules')
    op.drop_table('schedules')
    op.drop_index(op.f('ix_tle_cache_satellite_group'), table_name='tle_cache')
    op.drop_index(op.f('ix_tle_cache_norad_id'), table_name='tle_cache')
    op.drop_table('tle_cache')