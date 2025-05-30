"""add_author_profile_fields_to_user

Revision ID: a3ef43f3faa6
Revises: ab7be35a23ee
Create Date: 2025-05-18 00:09:28.574547

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
import sqlmodel


# revision identifiers, used by Alembic.
revision: str = 'a3ef43f3faa6'
down_revision: Union[str, None] = 'ab7be35a23ee'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('user', sa.Column('profile_picture_url', sa.String(), nullable=True))
    op.add_column('user', sa.Column('bio', sa.String(length=300), nullable=True))
    op.add_column('user', sa.Column('website_url', sa.String(), nullable=True))
    op.add_column('user', sa.Column('linkedin_url', sa.String(), nullable=True))
    op.add_column('user', sa.Column('github_url', sa.String(), nullable=True))
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('user', 'github_url')
    op.drop_column('user', 'linkedin_url')
    op.drop_column('user', 'website_url')
    op.drop_column('user', 'bio')
    op.drop_column('user', 'profile_picture_url')
    # ### end Alembic commands ###