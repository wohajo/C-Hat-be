"""empty message

Revision ID: 2a3a7cef9730
Revises: f94ce896528f
Create Date: 2021-05-05 20:14:27.972847

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '2a3a7cef9730'
down_revision = 'f94ce896528f'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('messages', sa.Column('receiverId', sa.Integer(), nullable=False))
    op.add_column('messages', sa.Column('senderId', sa.Integer(), nullable=False))
    op.drop_constraint('messages_user_from_id_fkey', 'messages', type_='foreignkey')
    op.drop_constraint('messages_user_to_id_fkey', 'messages', type_='foreignkey')
    op.create_foreign_key(None, 'messages', 'users', ['senderId'], ['id'])
    op.create_foreign_key(None, 'messages', 'users', ['receiverId'], ['id'])
    op.drop_column('messages', 'user_to_id')
    op.drop_column('messages', 'user_from_id')
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('messages', sa.Column('user_from_id', sa.INTEGER(), autoincrement=False, nullable=False))
    op.add_column('messages', sa.Column('user_to_id', sa.INTEGER(), autoincrement=False, nullable=False))
    op.drop_constraint(None, 'messages', type_='foreignkey')
    op.drop_constraint(None, 'messages', type_='foreignkey')
    op.create_foreign_key('messages_user_to_id_fkey', 'messages', 'users', ['user_to_id'], ['id'])
    op.create_foreign_key('messages_user_from_id_fkey', 'messages', 'users', ['user_from_id'], ['id'])
    op.drop_column('messages', 'senderId')
    op.drop_column('messages', 'receiverId')
    # ### end Alembic commands ###
