"""Add LLM evidence and PoC columns to vulnerabilities

Revision ID: 003_llm_evidence_poc
Revises: 002_enterprise
Create Date: 2026-04-12 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '003_llm_evidence_poc'
down_revision: Union[str, None] = '002_enterprise'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('vulnerabilities', sa.Column('llm_evidence', sa.Text(), nullable=True))
    op.add_column('vulnerabilities', sa.Column('llm_poc', sa.Text(), nullable=True))


def downgrade() -> None:
    op.drop_column('vulnerabilities', 'llm_poc')
    op.drop_column('vulnerabilities', 'llm_evidence')
