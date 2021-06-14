"""empty message

Revision ID: 1625d9aa09b4
Revises: 
Create Date: 2021-06-08 11:14:01.891241

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import mysql

# revision identifiers, used by Alembic.
revision = '1625d9aa09b4'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('machine', schema=None) as batch_op:
        batch_op.alter_column('platform',
               existing_type=mysql.VARCHAR(collation='utf8mb4_bin', length=128),
               type_=sa.String(length=32),
               existing_nullable=True)

    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('machine', schema=None) as batch_op:
        batch_op.alter_column('platform',
               existing_type=sa.String(length=32),
               type_=mysql.VARCHAR(collation='utf8mb4_bin', length=128),
               existing_nullable=True)

    # ### end Alembic commands ###
