"""create tables

Revision ID: 0ebaa362d4ec
Revises: 
Create Date: 2020-12-07 18:09:35.181693

"""
from alembic import op
import sqlalchemy as sa
from app.connects.postgres.session import engine
from app.connects.postgres.base import DBBase
from app.models.balance import Balance

# revision identifiers, used by Alembic.
revision = '0ebaa362d4ec'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    DBBase.metadata.create_all(bind=engine)


def downgrade():
    DBBase.metadata.drop_all(bind=engine)
    # op.drop_table("operations")
    # op.drop_table("balances")
    # op.drop_table("users")
