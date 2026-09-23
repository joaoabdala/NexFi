"""Cria um usuário administrador — para o primeiro acesso em produção (Neon).

Diferente de `app.seeds.seed`, não cria dados de exemplo nem chama `create_all`: o schema
deve existir via `alembic upgrade head`. A senha é pedida no terminal (não fica no histórico).

Uso:  python -m app.seeds.create_admin
"""

from getpass import getpass

from pydantic import ValidationError as PydanticValidationError

from app.core.exceptions import NexFiError
from app.db.session import SessionLocal, engine
from app.models.enums import UserRole
from app.schemas.admin import AdminUserCreate
from app.services import admin_user_service


def run() -> None:
    print(f"Banco: {engine.url.render_as_string(hide_password=True)}")
    email = input("E-mail: ").strip()
    name = input("Nome: ").strip()
    password = getpass("Senha (mín. 8 caracteres): ")
    if password != getpass("Confirme a senha: "):
        raise SystemExit("As senhas não conferem.")

    try:
        payload = AdminUserCreate(email=email, name=name, password=password, role=UserRole.ADMIN)
    except PydanticValidationError as exc:
        raise SystemExit(f"Dados inválidos: {exc.errors()[0]['msg']}") from exc

    db = SessionLocal()
    try:
        user = admin_user_service.create_user(db, payload)
    except NexFiError as exc:
        raise SystemExit(exc.message) from exc
    finally:
        db.close()
    print(f"Administrador criado: {user.email}")


if __name__ == "__main__":
    run()
