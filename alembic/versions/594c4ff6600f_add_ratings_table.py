"""add ratings table

Revision ID: 594c4ff6600f
Revises: 43aa16ff3dd5
Create Date: 2025-05-16 22:53:51.851649

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '594c4ff6600f'
down_revision: Union[str, None] = '43aa16ff3dd5'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'ratings',
        sa.Column('id', sa.Integer, primary_key=True),
        sa.Column('client_id', sa.Integer, sa.ForeignKey('users.id'), nullable=False),
        sa.Column('master_id', sa.Integer, sa.ForeignKey('users.id'), nullable=False),
        sa.Column('order_id', sa.Integer, sa.ForeignKey('orders.id'), nullable=False),
        sa.Column('score', sa.Integer, nullable=False),
        sa.Column('comment', sa.Text, nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now())
    )

def downgrade() -> None:
    op.drop_table('ratings')
