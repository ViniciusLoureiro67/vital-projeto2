"""add_finalizado_pago_to_checklists

Revision ID: 001
Revises: 
Create Date: 2024-01-01 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '001'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Adiciona colunas finalizado e pago na tabela checklists
    op.add_column('checklists', sa.Column('finalizado', sa.Boolean(), nullable=False, server_default='false'))
    op.add_column('checklists', sa.Column('pago', sa.Boolean(), nullable=False, server_default='false'))


def downgrade() -> None:
    # Remove as colunas
    op.drop_column('checklists', 'pago')
    op.drop_column('checklists', 'finalizado')

