
"""update_all

Revision ID: 9da7ac428d9b
Revises: 40a1132ddc9b
Create Date: 2026-10-20 09:53:31.731132
"""

from typing import Sequence, Union

from alembic import op
from pgvector.sqlalchemy import VECTOR


# revision identifiers, used by Alembic.
revision: str = "9da7ac428d9b"
down_revision: Union[str, Sequence[str], None] = "40a1132ddc9b"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.alter_column(
        "document_chunks",
        "embedding",
        existing_type=VECTOR(dim=1536),
        nullable=False,
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.alter_column(
        "document_chunks",
        "embedding",
        existing_type=VECTOR(dim=1536),
        nullable=True,
    )

