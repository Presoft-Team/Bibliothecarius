"""add title to conversations

Revision ID: c3f4a91d7e2b
Revises: bb08f6e387fa
Create Date: 2026-08-07 09:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = 'c3f4a91d7e2b'
down_revision: Union[str, None] = 'bb08f6e387fa'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Nullable — existing conversations just fall back to displaying "provider/model" in the
    # frontend (auto-titling only fires on a conversation's first message) until renamed.
    op.add_column('conversations', sa.Column('title', sa.String(), nullable=True))


def downgrade() -> None:
    op.drop_column('conversations', 'title')
