"""add data to students table

Revision ID: 45023da41179
Revises: 0756bd6b25f1
Create Date: 2018-09-09 16:28:16.030541

"""
from alembic import op
import sqlalchemy as sa

from models import Student


# revision identifiers, used by Alembic.
revision = '45023da41179'
down_revision = '0756bd6b25f1'
branch_labels = None
depends_on = None


def upgrade():
    op.bulk_insert(Student.__table__, [
        {'name': 'Liam Howlett'},
        {'name': 'Keith Flint'},
        {'name': 'Maxim Reality'},
    ])

def downgrade():
    pass
