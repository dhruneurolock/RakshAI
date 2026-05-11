"""Initial migration

Revision ID: 001
Revises: 
Create Date: 2024-01-20 10:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '001'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create scans table
    op.create_table('scans',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('scan_id', sa.String(), nullable=False),
        sa.Column('target_url', sa.String(), nullable=False),
        sa.Column('status', sa.Enum('pending', 'running', 'completed', 'failed', 'cancelled', name='scanstatus'), nullable=False),
        sa.Column('progress_percentage', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('current_phase', sa.String(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('started_at', sa.DateTime(), nullable=True),
        sa.Column('completed_at', sa.DateTime(), nullable=True),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('total_findings', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('critical_count', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('high_count', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('medium_count', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('low_count', sa.Integer(), nullable=False, server_default='0'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('scan_id')
    )
    op.create_index('idx_scans_status', 'scans', ['status'])
    op.create_index('idx_scans_created_at', 'scans', ['created_at'])

    # Create endpoints table
    op.create_table('endpoints',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('scan_id', sa.String(), nullable=False),
        sa.Column('url', sa.String(), nullable=False),
        sa.Column('method', sa.String(), nullable=False),
        sa.Column('parameters', postgresql.JSONB(), nullable=True),
        sa.Column('headers', postgresql.JSONB(), nullable=True),
        sa.Column('cookies', postgresql.JSONB(), nullable=True),
        sa.Column('forms', postgresql.JSONB(), nullable=True),
        sa.Column('discovered_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['scan_id'], ['scans.scan_id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_endpoints_scan_id', 'endpoints', ['scan_id'])

    # Create vulnerabilities table
    op.create_table('vulnerabilities',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('scan_id', sa.String(), nullable=False),
        sa.Column('vuln_id', sa.String(), nullable=False),
        sa.Column('title', sa.String(), nullable=False),
        sa.Column('description', sa.Text(), nullable=False),
        sa.Column('severity', sa.Enum('critical', 'high', 'medium', 'low', 'info', name='severity'), nullable=False),
        sa.Column('owasp_category', sa.String(), nullable=False),
        sa.Column('cwe_id', sa.String(), nullable=True),
        sa.Column('cvss_score', sa.Float(), nullable=True),
        sa.Column('confidence', sa.Float(), nullable=False),
        sa.Column('affected_endpoint', sa.String(), nullable=False),
        sa.Column('request_data', postgresql.JSONB(), nullable=True),
        sa.Column('response_data', postgresql.JSONB(), nullable=True),
        sa.Column('evidence', postgresql.JSONB(), nullable=True),
        sa.Column('remediation', sa.Text(), nullable=True),
        sa.Column('is_validated', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('validation_notes', sa.Text(), nullable=True),
        sa.Column('discovered_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['scan_id'], ['scans.scan_id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('vuln_id')
    )
    op.create_index('idx_vulnerabilities_scan_id', 'vulnerabilities', ['scan_id'])
    op.create_index('idx_vulnerabilities_severity', 'vulnerabilities', ['severity'])
    op.create_index('idx_vulnerabilities_owasp', 'vulnerabilities', ['owasp_category'])

    # Create attack_plans table
    op.create_table('attack_plans',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('scan_id', sa.String(), nullable=False),
        sa.Column('endpoint_id', sa.Integer(), nullable=False),
        sa.Column('plan_data', postgresql.JSONB(), nullable=False),
        sa.Column('total_tests', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['scan_id'], ['scans.scan_id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['endpoint_id'], ['endpoints.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_attack_plans_scan_id', 'attack_plans', ['scan_id'])

    # Create reports table
    op.create_table('reports',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('report_id', sa.String(), nullable=False),
        sa.Column('scan_id', sa.String(), nullable=False),
        sa.Column('format', sa.Enum('xml', 'json', name='reportformat'), nullable=False),
        sa.Column('content', sa.Text(), nullable=False),
        sa.Column('generated_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['scan_id'], ['scans.scan_id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('report_id')
    )
    op.create_index('idx_reports_scan_id', 'reports', ['scan_id'])


def downgrade() -> None:
    op.drop_index('idx_reports_scan_id', table_name='reports')
    op.drop_table('reports')
    op.drop_index('idx_attack_plans_scan_id', table_name='attack_plans')
    op.drop_table('attack_plans')
    op.drop_index('idx_vulnerabilities_owasp', table_name='vulnerabilities')
    op.drop_index('idx_vulnerabilities_severity', table_name='vulnerabilities')
    op.drop_index('idx_vulnerabilities_scan_id', table_name='vulnerabilities')
    op.drop_table('vulnerabilities')
    op.drop_index('idx_endpoints_scan_id', table_name='endpoints')
    op.drop_table('endpoints')
    op.drop_index('idx_scans_created_at', table_name='scans')
    op.drop_index('idx_scans_status', table_name='scans')
    op.drop_table('scans')
    sa.Enum(name='reportformat').drop(op.get_bind())
    sa.Enum(name='severity').drop(op.get_bind())
    sa.Enum(name='scanstatus').drop(op.get_bind())
