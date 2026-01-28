"""merge_chat_assessment_migration

Revision ID: 27f1a3e11c30
Revises: 9294fdf6e9a0, a1b2c3d4e5f6
Create Date: 2025-08-28 11:17:39.782285

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '27f1a3e11c30'
down_revision: Union[str, None] = ('9294fdf6e9a0', 'a1b2c3d4e5f6')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
