"""Add timezone support to DateTime columns

Revision ID: 002
Revises: 001
Create Date: 2026-08-10 05:14:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '002'
down_revision = '001'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # PostgreSQL: Alter DateTime columns to TIMESTAMPTZ (timezone-aware)
    # Note: This migration assumes PostgreSQL. For other databases, adjust accordingly.
    
    # TLE Cache table
    op.execute('ALTER TABLE tle_cache ALTER COLUMN fetched_at TYPE TIMESTAMPTZ USING fetched_at AT TIME ZONE \'UTC\'')
    
    # Schedules table
    op.execute('ALTER TABLE schedules ALTER COLUMN start_time TYPE TIMESTAMPTZ USING start_time AT TIME ZONE \'UTC\'')
    op.execute('ALTER TABLE schedules ALTER COLUMN end_time TYPE TIMESTAMPTZ USING end_time AT TIME ZONE \'UTC\'')
    op.execute('ALTER TABLE schedules ALTER COLUMN created_at TYPE TIMESTAMPTZ USING created_at AT TIME ZONE \'UTC\'')
    op.execute('ALTER TABLE schedules ALTER COLUMN updated_at TYPE TIMESTAMPTZ USING updated_at AT TIME ZONE \'UTC\'')
    
    # Conflicts table
    op.execute('ALTER TABLE conflicts ALTER COLUMN overlap_start TYPE TIMESTAMPTZ USING overlap_start AT TIME ZONE \'UTC\'')
    op.execute('ALTER TABLE conflicts ALTER COLUMN overlap_end TYPE TIMESTAMPTZ USING overlap_end AT TIME ZONE \'UTC\'')
    op.execute('ALTER TABLE conflicts ALTER COLUMN created_at TYPE TIMESTAMPTZ USING created_at AT TIME ZONE \'UTC\'')
    
    # Recommendations table
    op.execute('ALTER TABLE recommendations ALTER COLUMN created_at TYPE TIMESTAMPTZ USING created_at AT TIME ZONE \'UTC\'')


def downgrade() -> None:
    # Revert to TIMESTAMP (without timezone)
    
    # TLE Cache table
    op.execute('ALTER TABLE tle_cache ALTER COLUMN fetched_at TYPE TIMESTAMP')
    
    # Schedules table
    op.execute('ALTER TABLE schedules ALTER COLUMN start_time TYPE TIMESTAMP')
    op.execute('ALTER TABLE schedules ALTER COLUMN end_time TYPE TIMESTAMP')
    op.execute('ALTER TABLE schedules ALTER COLUMN created_at TYPE TIMESTAMP')
    op.execute('ALTER TABLE schedules ALTER COLUMN updated_at TYPE TIMESTAMP')
    
    # Conflicts table
    op.execute('ALTER TABLE conflicts ALTER COLUMN overlap_start TYPE TIMESTAMP')
    op.execute('ALTER TABLE conflicts ALTER COLUMN overlap_end TYPE TIMESTAMP')
    op.execute('ALTER TABLE conflicts ALTER COLUMN created_at TYPE TIMESTAMP')
    
    # Recommendations table
    op.execute('ALTER TABLE recommendations ALTER COLUMN created_at TYPE TIMESTAMP')
