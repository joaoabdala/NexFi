"""add user role

Revision ID: 877dd7756903
Revises: 75952d1bc0b4
Create Date: 2026-07-28 15:12:27.435488

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
import app.db.types

from app.core.config import settings


revision: str = '877dd7756903'
down_revision: Union[str, None] = '75952d1bc0b4'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # server_default garante que usuários já existentes recebam 'USER' automaticamente
    # (a coluna é NOT NULL); o default da aplicação continua vindo do model SQLAlchemy.
    op.add_column(
        'users',
        sa.Column(
            'role',
            sa.Enum('ADMIN', 'USER', name='userrole', native_enum=False, length=16),
            nullable=False,
            server_default='USER',
        ),
    )
    # O usuário demo criado pelo seed (ou já existente em bancos anteriores a esta
    # migration) vira administrador, para que o painel de administração seja acessível
    # imediatamente sem passo manual.
    users = sa.table('users', sa.column('email', sa.String), sa.column('role', sa.String))
    op.execute(
        users.update()
        .where(users.c.email == settings.SEED_ADMIN_EMAIL.lower())
        .values(role='ADMIN')
    )


def downgrade() -> None:
    op.drop_column('users', 'role')
