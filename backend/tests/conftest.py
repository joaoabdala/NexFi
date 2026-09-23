from datetime import date
from decimal import Decimal

import pytest
from sqlalchemy import create_engine, event
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app.core.security import hash_password
from app.db.base import Base
from app.models import *  # noqa: F401,F403 — garante que todos os models registrem no metadata
from app.models.account import Account
from app.models.category import Category
from app.models.enums import AccountType, CategoryKind
from app.models.institution import FinancialInstitution
from app.models.user import User


@pytest.fixture()
def db() -> Session:
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )

    @event.listens_for(engine, "connect")
    def _enable_sqlite_foreign_keys(dbapi_connection, connection_record):
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()

    Base.metadata.create_all(bind=engine)
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()
        engine.dispose()


@pytest.fixture()
def user(db: Session) -> User:
    u = User(email="test@nexfi.app", password_hash=hash_password("senha12345"), name="Test User")
    db.add(u)
    db.commit()
    db.refresh(u)
    return u


@pytest.fixture()
def institution(db: Session, user: User) -> FinancialInstitution:
    inst = FinancialInstitution(user_id=user.id, name="Banco Teste")
    db.add(inst)
    db.commit()
    db.refresh(inst)
    return inst


def make_account(
    db: Session,
    user: User,
    institution: FinancialInstitution,
    name: str = "Conta Teste",
    initial_balance: Decimal = Decimal("1000.00"),
    account_type: AccountType = AccountType.CONTA_CORRENTE,
    include_available: bool = True,
    include_invested: bool = False,
) -> Account:
    account = Account(
        user_id=user.id,
        institution_id=institution.id,
        name=name,
        type=account_type,
        initial_balance=initial_balance,
        initial_balance_date=date(2026, 1, 1),
        include_in_available_worth=include_available,
        include_in_invested_worth=include_invested,
    )
    db.add(account)
    db.commit()
    db.refresh(account)
    return account


def make_category(
    db: Session, user: User, name: str = "Categoria Teste", kind: CategoryKind = CategoryKind.DESPESA
) -> Category:
    category = Category(user_id=user.id, name=name, kind=kind)
    db.add(category)
    db.commit()
    db.refresh(category)
    return category


@pytest.fixture()
def account(db: Session, user: User, institution: FinancialInstitution) -> Account:
    return make_account(db, user, institution)


@pytest.fixture()
def account2(db: Session, user: User, institution: FinancialInstitution) -> Account:
    return make_account(db, user, institution, name="Conta Teste 2", initial_balance=Decimal("500.00"))


@pytest.fixture()
def expense_category(db: Session, user: User) -> Category:
    return make_category(db, user, "Despesa Teste", CategoryKind.DESPESA)


@pytest.fixture()
def income_category(db: Session, user: User) -> Category:
    return make_category(db, user, "Receita Teste", CategoryKind.RECEITA)
