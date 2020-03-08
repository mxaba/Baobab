"""Add file table

Revision ID: 5fe8721c7eb8
Revises: 2717ef90a874
Create Date: 2020-03-08 11:33:44.022766

"""

# revision identifiers, used by Alembic.
revision = '5fe8721c7eb8'
down_revision = '2717ef90a874'

from alembic import op
import sqlalchemy as sa


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('file',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('file_name', sa.String(length=50), nullable=False),
    sa.Column('mime_type', sa.String(length=50), nullable=False),
    sa.Column('guid', sa.String(length=50), nullable=False),
    sa.PrimaryKeyConstraint('id')
    )
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_table('file')
    # ### end Alembic commands ###
