"""merge_multiple_heads

Revision ID: d2f9a89ff6fc
Revises: add_forum_reports_table, add_forum_reports_table_simple
Create Date: 2025-08-23 18:35:15.260240

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'd2f9a89ff6fc'
down_revision: Union[str, None] = ('add_forum_reports_table', 'add_forum_reports_table_simple')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
