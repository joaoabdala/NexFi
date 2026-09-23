"""Popula o banco com dados de desenvolvimento (usuário demo, contas, categorias,
transações, cartão, financiamento) para que o Dashboard já nasça com dados reais.

Uso: python -m app.seeds.seed
"""

import uuid
from datetime import date, timedelta
from decimal import Decimal

from app.core.config import settings
from app.core.security import hash_password
from app.db.base import Base
from app.db.session import SessionLocal, engine
from app.models.account import Account
from app.models.budget import Budget
from app.models.category import Category
from app.models.enums import (
    AccountType,
    AmortizationType,
    CategoryKind,
    CommitmentType,
    RecurrenceFrequency,
    TransactionStatus,
    TransactionType,
    UserRole,
)
from app.models.goal import FinancialGoal
from app.models.institution import FinancialInstitution
from app.models.recurrence import RecurrenceRule
from app.models.transaction import Transaction
from app.models.user import User
from app.schemas.card import CreditCardCreate, CreditCardPurchaseCreate
from app.schemas.financing import AmortizationCreate, FinancialCommitmentCreate, InstallmentPayRequest
from app.schemas.transfer import TransferCreate
from app.services import card_service, financing_service, purchase_service, transfer_service
from app.utils.dates import add_months


def add_months_ago(months: int, day: int | None = None) -> date:
    base = date.today()
    result = add_months(base, -months)
    if day:
        import calendar

        last_day = calendar.monthrange(result.year, result.month)[1]
        result = result.replace(day=min(day, last_day))
    return result


def run() -> None:
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        existing = db.query(User).filter(User.email == settings.SEED_ADMIN_EMAIL.lower()).first()
        if existing:
            print(f"Usuário demo '{settings.SEED_ADMIN_EMAIL}' já existe — seed ignorado.")
            return

        user = User(
            email=settings.SEED_ADMIN_EMAIL.lower(),
            password_hash=hash_password(settings.SEED_ADMIN_PASSWORD),
            name=settings.SEED_ADMIN_NAME,
            role=UserRole.ADMIN,
        )
        db.add(user)
        db.commit()
        db.refresh(user)
        user_id = user.id

        # --- Instituições ---
        mercado_pago = FinancialInstitution(user_id=user_id, name="Mercado Pago", short_name="MP")
        nubank = FinancialInstitution(user_id=user_id, name="Nubank", short_name="Nu")
        itau = FinancialInstitution(user_id=user_id, name="Itaú", short_name="Itaú")
        db.add_all([mercado_pago, nubank, itau])
        db.commit()

        # --- Contas ---
        mp_saldo = Account(
            user_id=user_id,
            institution_id=mercado_pago.id,
            name="Saldo",
            type=AccountType.CONTA_DIGITAL,
            initial_balance=Decimal("5000.00"),
            initial_balance_date=add_months_ago(6),
            include_in_available_worth=True,
            include_in_invested_worth=False,
        )
        mp_cofrinho = Account(
            user_id=user_id,
            institution_id=mercado_pago.id,
            name="Cofrinho Reserva",
            type=AccountType.COFRINHO_RESERVA,
            initial_balance=Decimal("2000.00"),
            initial_balance_date=add_months_ago(6),
            include_in_available_worth=True,
            include_in_invested_worth=False,
        )
        nu_conta = Account(
            user_id=user_id,
            institution_id=nubank.id,
            name="Conta",
            type=AccountType.CONTA_DIGITAL,
            initial_balance=Decimal("1200.00"),
            initial_balance_date=add_months_ago(6),
            include_in_available_worth=True,
            include_in_invested_worth=False,
        )
        itau_invest = Account(
            user_id=user_id,
            institution_id=itau.id,
            name="CDB Itaú",
            type=AccountType.INVESTIMENTO,
            initial_balance=Decimal("10000.00"),
            initial_balance_date=add_months_ago(6),
            include_in_available_worth=False,
            include_in_invested_worth=True,
        )
        db.add_all([mp_saldo, mp_cofrinho, nu_conta, itau_invest])
        db.commit()
        for a in (mp_saldo, mp_cofrinho, nu_conta, itau_invest):
            db.refresh(a)

        # --- Categorias ---
        def make_category(name: str, kind: CategoryKind, parent: Category | None = None) -> Category:
            cat = Category(user_id=user_id, name=name, kind=kind, parent_id=parent.id if parent else None)
            db.add(cat)
            db.commit()
            db.refresh(cat)
            return cat

        moradia = make_category("Moradia", CategoryKind.DESPESA)
        cat_aluguel = make_category("Aluguel", CategoryKind.DESPESA, moradia)
        cat_energia = make_category("Energia", CategoryKind.DESPESA, moradia)
        make_category("Internet", CategoryKind.DESPESA, moradia)
        make_category("Condomínio", CategoryKind.DESPESA, moradia)

        transporte = make_category("Transporte", CategoryKind.DESPESA)
        cat_combustivel = make_category("Combustível", CategoryKind.DESPESA, transporte)
        make_category("Manutenção", CategoryKind.DESPESA, transporte)
        make_category("Seguro", CategoryKind.DESPESA, transporte)
        make_category("Estacionamento", CategoryKind.DESPESA, transporte)

        alimentacao = make_category("Alimentação", CategoryKind.DESPESA)
        cat_mercado = make_category("Mercado", CategoryKind.DESPESA, alimentacao)
        cat_restaurante = make_category("Restaurante", CategoryKind.DESPESA, alimentacao)
        make_category("Delivery", CategoryKind.DESPESA, alimentacao)

        cat_lazer = make_category("Lazer", CategoryKind.DESPESA)
        cat_salario = make_category("Salário", CategoryKind.RECEITA)
        make_category("Freelance", CategoryKind.RECEITA)
        make_category("Outros", CategoryKind.AMBOS)

        # --- Transações históricas (últimos 3 meses): salário, aluguel, mercado, lazer ---
        for months_ago in range(3, -1, -1):
            competence = add_months_ago(months_ago, day=5)
            db.add(
                Transaction(
                    user_id=user_id,
                    account_id=nu_conta.id,
                    category_id=cat_salario.id,
                    description="Salário",
                    type=TransactionType.RECEITA,
                    amount=Decimal("8000.00"),
                    competence_date=competence,
                    payment_date=competence,
                    status=TransactionStatus.CONFIRMADA,
                    origin="MANUAL",
                )
            )
            db.add(
                Transaction(
                    user_id=user_id,
                    account_id=nu_conta.id,
                    category_id=cat_aluguel.id,
                    description="Aluguel",
                    type=TransactionType.DESPESA,
                    amount=Decimal("1800.00"),
                    competence_date=add_months_ago(months_ago, day=10),
                    payment_date=add_months_ago(months_ago, day=10),
                    status=TransactionStatus.CONFIRMADA,
                    origin="MANUAL",
                )
            )
            db.add(
                Transaction(
                    user_id=user_id,
                    account_id=mp_saldo.id,
                    category_id=cat_mercado.id,
                    description="Supermercado",
                    type=TransactionType.DESPESA,
                    amount=Decimal("620.00"),
                    competence_date=add_months_ago(months_ago, day=15),
                    payment_date=add_months_ago(months_ago, day=15),
                    status=TransactionStatus.CONFIRMADA,
                    origin="MANUAL",
                )
            )
            db.add(
                Transaction(
                    user_id=user_id,
                    account_id=mp_saldo.id,
                    category_id=cat_energia.id,
                    description="Energia elétrica",
                    type=TransactionType.DESPESA,
                    amount=Decimal("210.00"),
                    competence_date=add_months_ago(months_ago, day=20),
                    payment_date=add_months_ago(months_ago, day=20),
                    status=TransactionStatus.CONFIRMADA,
                    origin="MANUAL",
                )
            )
            db.add(
                Transaction(
                    user_id=user_id,
                    account_id=mp_saldo.id,
                    category_id=cat_lazer.id,
                    description="Cinema",
                    type=TransactionType.DESPESA,
                    amount=Decimal("90.00"),
                    competence_date=add_months_ago(months_ago, day=22),
                    payment_date=add_months_ago(months_ago, day=22),
                    status=TransactionStatus.CONFIRMADA,
                    origin="MANUAL",
                )
            )
        db.commit()

        # --- Transferência: Saldo -> Cofrinho ---
        transfer_service.create_transfer(
            db,
            user_id,
            TransferCreate(
                from_account_id=mp_saldo.id,
                to_account_id=mp_cofrinho.id,
                amount=Decimal("500.00"),
                date=add_months_ago(1, day=3),
                description="Reforço reserva de emergência",
            ),
        )

        # --- Rendimentos ---
        for months_ago in range(2, -1, -1):
            db.add(
                Transaction(
                    user_id=user_id,
                    account_id=mp_cofrinho.id,
                    category_id=None,
                    description="Rendimento cofrinho",
                    type=TransactionType.RENDIMENTO,
                    amount=Decimal("20.40"),
                    competence_date=add_months_ago(months_ago, day=28),
                    payment_date=add_months_ago(months_ago, day=28),
                    status=TransactionStatus.CONFIRMADA,
                    origin="MANUAL",
                )
            )
            db.add(
                Transaction(
                    user_id=user_id,
                    account_id=itau_invest.id,
                    category_id=None,
                    description="Rendimento CDB",
                    type=TransactionType.RENDIMENTO,
                    amount=Decimal("48.70"),
                    competence_date=add_months_ago(months_ago, day=28),
                    payment_date=add_months_ago(months_ago, day=28),
                    status=TransactionStatus.CONFIRMADA,
                    origin="MANUAL",
                )
            )
        db.commit()

        # --- Cartão Nubank + compra parcelada ---
        card = card_service.create_card(
            db,
            user_id,
            CreditCardCreate(
                institution_id=nubank.id,
                name="Nubank Cartão",
                brand="Mastercard",
                last_digits="4321",
                credit_limit=Decimal("5000.00"),
                closing_day=5,
                due_day=12,
                default_payment_account_id=nu_conta.id,
            ),
        )
        purchase_service.create_purchase(
            db,
            user_id,
            card["id"],
            CreditCardPurchaseCreate(
                description="Notebook",
                total_amount=Decimal("6000.00"),
                installments_total=10,
                purchase_date=add_months_ago(1, day=18),
                category_id=None,
            ),
        )
        db.add(
            Transaction(
                user_id=user_id,
                account_id=None,
                category_id=cat_restaurante.id,
                description="Restaurante",
                type=TransactionType.DESPESA,
                amount=Decimal("150.00"),
                competence_date=add_months_ago(0, day=8),
                payment_date=None,
                status=TransactionStatus.CONFIRMADA,
                origin="CARTAO",
            )
        )
        db.commit()

        # --- Financiamento imobiliário ---
        commitment = financing_service.create_commitment(
            db,
            user_id,
            FinancialCommitmentCreate(
                institution_id=itau.id,
                type=CommitmentType.FINANCIAMENTO,
                name="Financiamento Apartamento",
                asset_value=Decimal("300000.00"),
                down_payment=Decimal("60000.00"),
                financed_amount=Decimal("45000.00"),
                interest_rate=Decimal("0.0089"),
                installments_total=48,
                default_installment_amount=Decimal("1050.00"),
                start_date=add_months_ago(15, day=10),
                due_day=10,
            ),
        )
        from app.repositories import financing_repository

        installments = financing_repository.list_installments(db, commitment["id"])
        for installment in installments[:15]:
            financing_service.pay_installment(
                db,
                user_id,
                commitment["id"],
                installment.id,
                InstallmentPayRequest(payment_date=installment.due_date, account_id=nu_conta.id),
            )
        financing_service.create_amortization(
            db,
            user_id,
            commitment["id"],
            AmortizationCreate(
                date=add_months_ago(0, day=10),
                paid_amount=Decimal("6800.00"),
                type=AmortizationType.REDUCAO_PRAZO,
                account_id=nu_conta.id,
                installment_numbers=list(range(41, 49)),
                note="Amortização extraordinária com bônus anual",
            ),
        )

        # --- Orçamentos ---
        db.add_all(
            [
                Budget(user_id=user_id, category_id=alimentacao.id, amount=Decimal("1200.00"), is_default=True),
                Budget(user_id=user_id, category_id=cat_lazer.id, amount=Decimal("500.00"), is_default=True),
            ]
        )

        # --- Meta financeira ---
        db.add(
            FinancialGoal(
                user_id=user_id,
                name="Reserva de emergência",
                target_amount=Decimal("20000.00"),
                current_amount=Decimal("0"),
                linked_account_id=mp_cofrinho.id,
                target_date=add_months(date.today(), 12),
            )
        )

        # --- Recorrência: Netflix ---
        db.add(
            RecurrenceRule(
                user_id=user_id,
                description="Netflix",
                type=TransactionType.DESPESA,
                amount=Decimal("39.90"),
                category_id=cat_lazer.id,
                account_id=nu_conta.id,
                frequency=RecurrenceFrequency.MENSAL,
                reference_day=15,
                start_date=date.today(),
            )
        )
        db.commit()

        print("Seed concluído com sucesso.")
        print(f"Usuário demo: {settings.SEED_ADMIN_EMAIL} / senha: {settings.SEED_ADMIN_PASSWORD}")
    finally:
        db.close()


if __name__ == "__main__":
    run()
