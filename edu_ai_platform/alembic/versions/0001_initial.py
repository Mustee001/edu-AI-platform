"""initial migration

Revision ID: 0001_initial
Revises: 
Create Date: 2025-11-19 00:00:00.000000
"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '0001_initial'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        'student',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('student_id', sa.String(), nullable=False),
        sa.Column('name', sa.String(), nullable=False),
        sa.Column('grade', sa.Integer(), nullable=False),
        sa.Column('class_id', sa.Integer(), nullable=True),
    )
    op.create_table(
        'lesson',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('item_id', sa.String(), nullable=False),
        sa.Column('subject', sa.String(), nullable=True),
        sa.Column('prompt', sa.String(), nullable=True),
        sa.Column('source', sa.String(), nullable=True),
    )
    op.create_table(
        'assignment',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('student_id', sa.String(), nullable=False),
        sa.Column('item_id', sa.String(), nullable=False),
        sa.Column('assigned_at', sa.String(), nullable=True),
    )
    op.create_table(
        'studentresponse',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('student_id', sa.String(), nullable=False),
        sa.Column('item_id', sa.String(), nullable=False),
        sa.Column('answer', sa.String(), nullable=True),
        sa.Column('correct', sa.Boolean(), nullable=True),
        sa.Column('submitted_at', sa.String(), nullable=True),
    )
    op.create_table(
        'classroom',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('name', sa.String(), nullable=False),
        sa.Column('teacher_id', sa.String(), nullable=True),
    )
    op.create_table(
        'refreshtoken',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('token', sa.Text(), nullable=False),
        sa.Column('username', sa.String(), nullable=True),
        sa.Column('created_at', sa.String(), nullable=True),
        sa.Column('expires_at', sa.String(), nullable=True),
        sa.Column('revoked', sa.Boolean(), nullable=True),
    )


def downgrade():
    op.drop_table('refreshtoken')
    op.drop_table('classroom')
    op.drop_table('studentresponse')
    op.drop_table('assignment')
    op.drop_table('lesson')
    op.drop_table('student')
