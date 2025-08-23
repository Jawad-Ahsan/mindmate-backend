"""make_appointment_dates_nullable_for_pending_approval

Revision ID: 9294fdf6e9a0
Revises: d2f9a89ff6fc
Create Date: 2025-08-23 18:35:20.433816

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '9294fdf6e9a0'
down_revision: Union[str, None] = 'd2f9a89ff6fc'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Make scheduled_start and scheduled_end nullable for pending approval appointments
    op.alter_column('appointments', 'scheduled_start',
                    existing_type=sa.DateTime(timezone=True),
                    nullable=True)
    op.alter_column('appointments', 'scheduled_end',
                    existing_type=sa.DateTime(timezone=True),
                    nullable=True)


def downgrade() -> None:
    """Downgrade schema."""
    # Make scheduled_start and scheduled_end non-nullable again
    op.alter_column('appointments', 'scheduled_start',
                    existing_type=sa.DateTime(timezone=True),
                    nullable=False)
    op.alter_column('appointments', 'scheduled_end',
                    existing_type=sa.DateTime(timezone=True),
                    nullable=False)
