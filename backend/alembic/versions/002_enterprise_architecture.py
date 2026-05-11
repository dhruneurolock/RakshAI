"""Add enterprise architecture fields

Revision ID: 002_enterprise
Revises: 001
Create Date: 2026-02-22 11:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '002_enterprise'
down_revision: Union[str, None] = '001'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add enterprise fields to scans table
    op.add_column('scans', sa.Column('policy', sa.JSON(), nullable=True))
    op.add_column('scans', sa.Column('strategy', sa.JSON(), nullable=True))
    op.add_column('scans', sa.Column('endpoints_discovered', sa.Integer(), nullable=True, server_default='0'))
    op.add_column('scans', sa.Column('attacks_planned', sa.Integer(), nullable=True, server_default='0'))
    op.add_column('scans', sa.Column('attacks_executed', sa.Integer(), nullable=True, server_default='0'))
    op.add_column('scans', sa.Column('validated_findings', sa.Integer(), nullable=True, server_default='0'))
    op.add_column('scans', sa.Column('false_positives', sa.Integer(), nullable=True, server_default='0'))
    
    # Add enterprise fields to vulnerabilities table
    op.add_column('vulnerabilities', sa.Column('vulnerability_type', sa.String(length=50), nullable=True))
    op.add_column('vulnerabilities', sa.Column('status', sa.String(length=50), nullable=True, server_default='UNVALIDATED'))
    op.add_column('vulnerabilities', sa.Column('validation_replays', sa.Integer(), nullable=True, server_default='0'))
    op.add_column('vulnerabilities', sa.Column('validation_count', sa.Integer(), nullable=True, server_default='0'))
    op.add_column('vulnerabilities', sa.Column('poc_screenshot_url', sa.String(length=500), nullable=True))
    op.add_column('vulnerabilities', sa.Column('poc_http_trace_url', sa.String(length=500), nullable=True))
    op.add_column('vulnerabilities', sa.Column('poc_curl_command', sa.Text(), nullable=True))
    op.add_column('vulnerabilities', sa.Column('llm_business_impact', sa.Text(), nullable=True))
    op.add_column('vulnerabilities', sa.Column('llm_remediation', sa.Text(), nullable=True))
    op.add_column('vulnerabilities', sa.Column('poc_generated_at', sa.DateTime(timezone=True), nullable=True))
    

def downgrade() -> None:
    # Drop enterprise fields from vulnerabilities table
    op.drop_column('vulnerabilities', 'poc_generated_at')
    op.drop_column('vulnerabilities', 'llm_remediation')
    op.drop_column('vulnerabilities', 'llm_business_impact')
    op.drop_column('vulnerabilities', 'poc_curl_command')
    op.drop_column('vulnerabilities', 'poc_http_trace_url')
    op.drop_column('vulnerabilities', 'poc_screenshot_url')
    op.drop_column('vulnerabilities', 'validation_count')
    op.drop_column('vulnerabilities', 'validation_replays')
    op.drop_column('vulnerabilities', 'status')
    op.drop_column('vulnerabilities', 'vulnerability_type')
    
    # Drop enterprise fields from scans table
    op.drop_column('scans', 'false_positives')
    op.drop_column('scans', 'validated_findings')
    op.drop_column('scans', 'attacks_executed')
    op.drop_column('scans', 'attacks_planned')
    op.drop_column('scans', 'endpoints_discovered')
    op.drop_column('scans', 'strategy')
    op.drop_column('scans', 'policy')
