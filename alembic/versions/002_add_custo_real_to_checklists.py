"""add_custo_real_to_checklists

Revision ID: 002
Revises: 001
Create Date: 2024-01-01 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '002'
down_revision = '001'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Adiciona coluna custo_real na tabela checklists
    op.add_column('checklists', sa.Column('custo_real', sa.Float(), nullable=True))


def downgrade() -> None:
    # Remove a coluna
    op.drop_column('checklists', 'custo_real')

