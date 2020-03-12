"""add company table

Revision ID: 34290351c8bd
Revises: ce88ff501e0e
Create Date: 2020-03-12 01:32:27.492272

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '34290351c8bd'
down_revision = 'ce88ff501e0e'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('company',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('name', sa.String(length=255), nullable=False),
    sa.Column('symbol', sa.String(length=8), nullable=False),
    sa.Column('market', sa.String(length=20), nullable=False),
    sa.Column('deleted', sa.Boolean(), nullable=True),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('symbol', 'market', name='unq_symbol_market')
    )
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_table('company')
    # ### end Alembic commands ###