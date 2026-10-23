"""check urgencia en triaje

Revision ID: f3b8d7621928
Revises: 3fb05b6732d6
Create Date: 2026-10-22 19:01:22.409040

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'f3b8d7621928'
down_revision: Union[str, Sequence[str], None] = '3fb05b6732d6'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_check_constraint(
        "triaje_urgencia_valida",
        "triaje",
        "urgencia IN ('baja', 'media', 'alta', 'urgente')",
    )
    


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_constraint("triaje_urgencia_valida", "triaje", type_="check")
    
