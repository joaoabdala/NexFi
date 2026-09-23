"""initial schema

Revision ID: 75952d1bc0b4
Revises:
Create Date: 2026-07-28 12:27:39.899943

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
import app.db.types


revision: str = '75952d1bc0b4'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Tabelas criadas em ordem topológica de dependência de FK. Um pequeno grupo
    # (transactions <-> credit_card_invoices/installments/amortizations/commitment_installments)
    # forma um ciclo genuíno via colunas nullable SET NULL; essas constraints específicas são
    # adicionadas via ALTER TABLE ao final, depois que todas as tabelas já existem.
    op.create_table('users',
    sa.Column('email', sa.String(length=255), nullable=False),
    sa.Column('password_hash', sa.String(length=255), nullable=False),
    sa.Column('name', sa.String(length=255), nullable=False),
    sa.Column('timezone', sa.String(length=64), nullable=False),
    sa.Column('locale', sa.String(length=16), nullable=False),
    sa.Column('is_active', sa.Boolean(), nullable=False),
    sa.Column('id', app.db.types.GUID(), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
    sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_users_email'), 'users', ['email'], unique=True)

    op.create_table('financial_institutions',
    sa.Column('user_id', app.db.types.GUID(), nullable=False),
    sa.Column('name', sa.String(length=255), nullable=False),
    sa.Column('short_name', sa.String(length=64), nullable=True),
    sa.Column('active', sa.Boolean(), nullable=False),
    sa.Column('note', sa.Text(), nullable=True),
    sa.Column('id', app.db.types.GUID(), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
    sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
    sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_financial_institutions_user_id'), 'financial_institutions', ['user_id'], unique=False)

    op.create_table('accounts',
    sa.Column('user_id', app.db.types.GUID(), nullable=False),
    sa.Column('institution_id', app.db.types.GUID(), nullable=False),
    sa.Column('name', sa.String(length=255), nullable=False),
    sa.Column('type', sa.Enum('CONTA_CORRENTE', 'CONTA_DIGITAL', 'POUPANCA', 'DINHEIRO', 'COFRINHO_RESERVA', 'INVESTIMENTO', 'OUTROS', name='accounttype', native_enum=False, length=32), nullable=False),
    sa.Column('initial_balance', sa.Numeric(precision=15, scale=2), nullable=False),
    sa.Column('initial_balance_date', sa.Date(), nullable=False),
    sa.Column('active', sa.Boolean(), nullable=False),
    sa.Column('include_in_available_worth', sa.Boolean(), nullable=False),
    sa.Column('include_in_invested_worth', sa.Boolean(), nullable=False),
    sa.Column('note', sa.Text(), nullable=True),
    sa.Column('deleted_at', sa.Date(), nullable=True),
    sa.Column('id', app.db.types.GUID(), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
    sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
    sa.ForeignKeyConstraint(['institution_id'], ['financial_institutions.id'], ondelete='RESTRICT'),
    sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_accounts_institution_id'), 'accounts', ['institution_id'], unique=False)
    op.create_index(op.f('ix_accounts_user_id'), 'accounts', ['user_id'], unique=False)

    op.create_table('categories',
    sa.Column('user_id', app.db.types.GUID(), nullable=False),
    sa.Column('parent_id', app.db.types.GUID(), nullable=True),
    sa.Column('name', sa.String(length=120), nullable=False),
    sa.Column('kind', sa.Enum('RECEITA', 'DESPESA', 'AMBOS', name='categorykind', native_enum=False, length=16), nullable=False),
    sa.Column('active', sa.Boolean(), nullable=False),
    sa.Column('id', app.db.types.GUID(), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
    sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
    sa.ForeignKeyConstraint(['parent_id'], ['categories.id'], ondelete='CASCADE'),
    sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_categories_parent_id'), 'categories', ['parent_id'], unique=False)
    op.create_index(op.f('ix_categories_user_id'), 'categories', ['user_id'], unique=False)

    op.create_table('transfers',
    sa.Column('user_id', app.db.types.GUID(), nullable=False),
    sa.Column('from_account_id', app.db.types.GUID(), nullable=False),
    sa.Column('to_account_id', app.db.types.GUID(), nullable=False),
    sa.Column('amount', sa.Numeric(precision=15, scale=2), nullable=False),
    sa.Column('date', sa.Date(), nullable=False),
    sa.Column('description', sa.String(length=255), nullable=True),
    sa.Column('note', sa.Text(), nullable=True),
    sa.Column('id', app.db.types.GUID(), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
    sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
    sa.ForeignKeyConstraint(['from_account_id'], ['accounts.id'], ondelete='RESTRICT'),
    sa.ForeignKeyConstraint(['to_account_id'], ['accounts.id'], ondelete='RESTRICT'),
    sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_transfers_from_account_id'), 'transfers', ['from_account_id'], unique=False)
    op.create_index(op.f('ix_transfers_to_account_id'), 'transfers', ['to_account_id'], unique=False)
    op.create_index(op.f('ix_transfers_user_id'), 'transfers', ['user_id'], unique=False)

    op.create_table('refresh_tokens',
    sa.Column('user_id', app.db.types.GUID(), nullable=False),
    sa.Column('token_hash', sa.String(length=128), nullable=False),
    sa.Column('expires_at', sa.DateTime(timezone=True), nullable=False),
    sa.Column('revoked_at', sa.DateTime(timezone=True), nullable=True),
    sa.Column('id', app.db.types.GUID(), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
    sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
    sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_refresh_tokens_token_hash'), 'refresh_tokens', ['token_hash'], unique=True)
    op.create_index(op.f('ix_refresh_tokens_user_id'), 'refresh_tokens', ['user_id'], unique=False)

    op.create_table('credit_cards',
    sa.Column('user_id', app.db.types.GUID(), nullable=False),
    sa.Column('institution_id', app.db.types.GUID(), nullable=False),
    sa.Column('name', sa.String(length=120), nullable=False),
    sa.Column('brand', sa.String(length=32), nullable=True),
    sa.Column('last_digits', sa.String(length=4), nullable=True),
    sa.Column('credit_limit', sa.Numeric(precision=15, scale=2), nullable=False),
    sa.Column('closing_day', sa.Integer(), nullable=False),
    sa.Column('due_day', sa.Integer(), nullable=False),
    sa.Column('default_payment_account_id', app.db.types.GUID(), nullable=False),
    sa.Column('active', sa.Boolean(), nullable=False),
    sa.Column('id', app.db.types.GUID(), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
    sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
    sa.ForeignKeyConstraint(['default_payment_account_id'], ['accounts.id'], ondelete='RESTRICT'),
    sa.ForeignKeyConstraint(['institution_id'], ['financial_institutions.id'], ondelete='RESTRICT'),
    sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_credit_cards_user_id'), 'credit_cards', ['user_id'], unique=False)

    op.create_table('credit_card_purchases',
    sa.Column('user_id', app.db.types.GUID(), nullable=False),
    sa.Column('card_id', app.db.types.GUID(), nullable=False),
    sa.Column('category_id', app.db.types.GUID(), nullable=True),
    sa.Column('description', sa.String(length=255), nullable=False),
    sa.Column('total_amount', sa.Numeric(precision=15, scale=2), nullable=False),
    sa.Column('installments_total', sa.Integer(), nullable=False),
    sa.Column('purchase_date', sa.Date(), nullable=False),
    sa.Column('id', app.db.types.GUID(), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
    sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
    sa.ForeignKeyConstraint(['card_id'], ['credit_cards.id'], ondelete='RESTRICT'),
    sa.ForeignKeyConstraint(['category_id'], ['categories.id'], ondelete='SET NULL'),
    sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_credit_card_purchases_card_id'), 'credit_card_purchases', ['card_id'], unique=False)
    op.create_index(op.f('ix_credit_card_purchases_user_id'), 'credit_card_purchases', ['user_id'], unique=False)

    op.create_table('financial_commitments',
    sa.Column('user_id', app.db.types.GUID(), nullable=False),
    sa.Column('institution_id', app.db.types.GUID(), nullable=False),
    sa.Column('type', sa.Enum('FINANCIAMENTO', 'EMPRESTIMO', 'CONSORCIO', 'OUTROS', name='commitmenttype', native_enum=False, length=16), nullable=False),
    sa.Column('name', sa.String(length=255), nullable=False),
    sa.Column('asset_value', sa.Numeric(precision=15, scale=2), nullable=True),
    sa.Column('down_payment', sa.Numeric(precision=15, scale=2), nullable=True),
    sa.Column('financed_amount', sa.Numeric(precision=15, scale=2), nullable=False),
    sa.Column('interest_rate', sa.Numeric(precision=9, scale=6), nullable=True),
    sa.Column('installments_total', sa.Integer(), nullable=False),
    sa.Column('default_installment_amount', sa.Numeric(precision=15, scale=2), nullable=False),
    sa.Column('start_date', sa.Date(), nullable=False),
    sa.Column('due_day', sa.Integer(), nullable=False),
    sa.Column('outstanding_balance', sa.Numeric(precision=15, scale=2), nullable=False),
    sa.Column('status', sa.Enum('ATIVO', 'QUITADO', 'CANCELADO', name='commitmentstatus', native_enum=False, length=16), nullable=False),
    sa.Column('note', sa.Text(), nullable=True),
    sa.Column('id', app.db.types.GUID(), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
    sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
    sa.ForeignKeyConstraint(['institution_id'], ['financial_institutions.id'], ondelete='RESTRICT'),
    sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_financial_commitments_user_id'), 'financial_commitments', ['user_id'], unique=False)

    op.create_table('financial_goals',
    sa.Column('user_id', app.db.types.GUID(), nullable=False),
    sa.Column('name', sa.String(length=255), nullable=False),
    sa.Column('target_amount', sa.Numeric(precision=15, scale=2), nullable=False),
    sa.Column('current_amount', sa.Numeric(precision=15, scale=2), nullable=False),
    sa.Column('linked_account_id', app.db.types.GUID(), nullable=True),
    sa.Column('target_date', sa.Date(), nullable=True),
    sa.Column('status', sa.Enum('EM_ANDAMENTO', 'CONCLUIDA', 'CANCELADA', name='goalstatus', native_enum=False, length=16), nullable=False),
    sa.Column('id', app.db.types.GUID(), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
    sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
    sa.ForeignKeyConstraint(['linked_account_id'], ['accounts.id'], ondelete='SET NULL'),
    sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_financial_goals_user_id'), 'financial_goals', ['user_id'], unique=False)

    op.create_table('budgets',
    sa.Column('user_id', app.db.types.GUID(), nullable=False),
    sa.Column('category_id', app.db.types.GUID(), nullable=False),
    sa.Column('amount', sa.Numeric(precision=15, scale=2), nullable=False),
    sa.Column('month', sa.Integer(), nullable=True),
    sa.Column('year', sa.Integer(), nullable=True),
    sa.Column('is_default', sa.Boolean(), nullable=False),
    sa.Column('id', app.db.types.GUID(), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
    sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
    sa.ForeignKeyConstraint(['category_id'], ['categories.id'], ondelete='CASCADE'),
    sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('user_id', 'category_id', 'month', 'year', name='uq_budget_scope')
    )
    op.create_index(op.f('ix_budgets_category_id'), 'budgets', ['category_id'], unique=False)
    op.create_index(op.f('ix_budgets_user_id'), 'budgets', ['user_id'], unique=False)

    op.create_table('recurrence_rules',
    sa.Column('user_id', app.db.types.GUID(), nullable=False),
    sa.Column('description', sa.String(length=255), nullable=False),
    sa.Column('type', sa.Enum('RECEITA', 'DESPESA', 'TRANSFERENCIA', 'RENDIMENTO', 'AJUSTE', 'PAGAMENTO_FATURA', 'PAGAMENTO_FINANCIAMENTO', 'AMORTIZACAO', name='transactiontype', native_enum=False, length=32), nullable=False),
    sa.Column('amount', sa.Numeric(precision=15, scale=2), nullable=False),
    sa.Column('category_id', app.db.types.GUID(), nullable=True),
    sa.Column('account_id', app.db.types.GUID(), nullable=False),
    sa.Column('frequency', sa.Enum('SEMANAL', 'MENSAL', 'ANUAL', 'PERSONALIZADA', name='recurrencefrequency', native_enum=False, length=16), nullable=False),
    sa.Column('reference_day', sa.Integer(), nullable=True),
    sa.Column('custom_interval_days', sa.Integer(), nullable=True),
    sa.Column('start_date', sa.Date(), nullable=False),
    sa.Column('end_date', sa.Date(), nullable=True),
    sa.Column('active', sa.Boolean(), nullable=False),
    sa.Column('last_generated_competence', sa.Date(), nullable=True),
    sa.Column('id', app.db.types.GUID(), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
    sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
    sa.ForeignKeyConstraint(['account_id'], ['accounts.id'], ondelete='CASCADE'),
    sa.ForeignKeyConstraint(['category_id'], ['categories.id'], ondelete='SET NULL'),
    sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_recurrence_rules_user_id'), 'recurrence_rules', ['user_id'], unique=False)

    # --- Grupo com dependência circular (via colunas nullable) ---
    # Criadas nesta ordem para que apenas os 4 FKs "de volta" para transactions
    # precisem ser adicionados depois; todo o resto já referencia tabelas existentes.
    op.create_table('credit_card_invoices',
    sa.Column('card_id', app.db.types.GUID(), nullable=False),
    sa.Column('competence', sa.Date(), nullable=False),
    sa.Column('closing_date', sa.Date(), nullable=False),
    sa.Column('due_date', sa.Date(), nullable=False),
    sa.Column('status', sa.Enum('ABERTA', 'FECHADA', 'PAGA', 'VENCIDA', name='invoicestatus', native_enum=False, length=16), nullable=False),
    sa.Column('payment_date', sa.Date(), nullable=True),
    sa.Column('payment_account_id', app.db.types.GUID(), nullable=True),
    sa.Column('payment_transaction_id', app.db.types.GUID(), nullable=True),
    sa.Column('id', app.db.types.GUID(), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
    sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
    sa.ForeignKeyConstraint(['card_id'], ['credit_cards.id'], ondelete='CASCADE'),
    sa.ForeignKeyConstraint(['payment_account_id'], ['accounts.id'], ondelete='RESTRICT'),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('card_id', 'competence', name='uq_invoice_card_competence')
    )
    op.create_index(op.f('ix_credit_card_invoices_card_id'), 'credit_card_invoices', ['card_id'], unique=False)

    op.create_table('credit_card_installments',
    sa.Column('purchase_id', app.db.types.GUID(), nullable=False),
    sa.Column('invoice_id', app.db.types.GUID(), nullable=False),
    sa.Column('number', sa.Integer(), nullable=False),
    sa.Column('amount', sa.Numeric(precision=15, scale=2), nullable=False),
    sa.Column('transaction_id', app.db.types.GUID(), nullable=True),
    sa.Column('id', app.db.types.GUID(), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
    sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
    sa.ForeignKeyConstraint(['invoice_id'], ['credit_card_invoices.id'], ondelete='RESTRICT'),
    sa.ForeignKeyConstraint(['purchase_id'], ['credit_card_purchases.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('purchase_id', 'number', name='uq_installment_purchase_number')
    )
    op.create_index(op.f('ix_credit_card_installments_invoice_id'), 'credit_card_installments', ['invoice_id'], unique=False)
    op.create_index(op.f('ix_credit_card_installments_purchase_id'), 'credit_card_installments', ['purchase_id'], unique=False)

    op.create_table('amortizations',
    sa.Column('user_id', app.db.types.GUID(), nullable=False),
    sa.Column('commitment_id', app.db.types.GUID(), nullable=False),
    sa.Column('date', sa.Date(), nullable=False),
    sa.Column('paid_amount', sa.Numeric(precision=15, scale=2), nullable=False),
    sa.Column('nominal_amortized_amount', sa.Numeric(precision=15, scale=2), nullable=False),
    sa.Column('discount_obtained', sa.Numeric(precision=15, scale=2), nullable=False),
    sa.Column('type', sa.Enum('REDUCAO_PRAZO', 'REDUCAO_PARCELA', name='amortizationtype', native_enum=False, length=32), nullable=False),
    sa.Column('account_id', app.db.types.GUID(), nullable=False),
    sa.Column('note', sa.Text(), nullable=True),
    sa.Column('transaction_id', app.db.types.GUID(), nullable=True),
    sa.Column('id', app.db.types.GUID(), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
    sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
    sa.ForeignKeyConstraint(['account_id'], ['accounts.id'], ondelete='RESTRICT'),
    sa.ForeignKeyConstraint(['commitment_id'], ['financial_commitments.id'], ondelete='CASCADE'),
    sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_amortizations_commitment_id'), 'amortizations', ['commitment_id'], unique=False)
    op.create_index(op.f('ix_amortizations_user_id'), 'amortizations', ['user_id'], unique=False)

    op.create_table('commitment_installments',
    sa.Column('commitment_id', app.db.types.GUID(), nullable=False),
    sa.Column('number', sa.Integer(), nullable=False),
    sa.Column('due_date', sa.Date(), nullable=False),
    sa.Column('original_amount', sa.Numeric(precision=15, scale=2), nullable=False),
    sa.Column('updated_amount', sa.Numeric(precision=15, scale=2), nullable=False),
    sa.Column('paid_amount', sa.Numeric(precision=15, scale=2), nullable=True),
    sa.Column('payment_date', sa.Date(), nullable=True),
    sa.Column('status', sa.Enum('PENDENTE', 'PAGA', 'AMORTIZADA', 'CANCELADA', name='commitmentinstallmentstatus', native_enum=False, length=16), nullable=False),
    sa.Column('transaction_id', app.db.types.GUID(), nullable=True),
    sa.Column('amortization_id', app.db.types.GUID(), nullable=True),
    sa.Column('id', app.db.types.GUID(), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
    sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
    sa.ForeignKeyConstraint(['amortization_id'], ['amortizations.id'], ondelete='SET NULL'),
    sa.ForeignKeyConstraint(['commitment_id'], ['financial_commitments.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('commitment_id', 'number', name='uq_commitment_installment_number')
    )
    op.create_index(op.f('ix_commitment_installments_commitment_id'), 'commitment_installments', ['commitment_id'], unique=False)

    op.create_table('transactions',
    sa.Column('user_id', app.db.types.GUID(), nullable=False),
    sa.Column('account_id', app.db.types.GUID(), nullable=True),
    sa.Column('category_id', app.db.types.GUID(), nullable=True),
    sa.Column('description', sa.String(length=255), nullable=False),
    sa.Column('type', sa.Enum('RECEITA', 'DESPESA', 'TRANSFERENCIA', 'RENDIMENTO', 'AJUSTE', 'PAGAMENTO_FATURA', 'PAGAMENTO_FINANCIAMENTO', 'AMORTIZACAO', name='transactiontype', native_enum=False, length=32), nullable=False),
    sa.Column('amount', sa.Numeric(precision=15, scale=2), nullable=False),
    sa.Column('competence_date', sa.Date(), nullable=False),
    sa.Column('payment_date', sa.Date(), nullable=True),
    sa.Column('status', sa.Enum('PENDENTE', 'CONFIRMADA', 'CANCELADA', name='transactionstatus', native_enum=False, length=16), nullable=False),
    sa.Column('note', sa.Text(), nullable=True),
    sa.Column('origin', sa.String(length=32), nullable=False),
    sa.Column('external_reference', sa.String(length=255), nullable=True),
    sa.Column('transfer_id', app.db.types.GUID(), nullable=True),
    sa.Column('card_installment_id', app.db.types.GUID(), nullable=True),
    sa.Column('invoice_id', app.db.types.GUID(), nullable=True),
    sa.Column('commitment_installment_id', app.db.types.GUID(), nullable=True),
    sa.Column('amortization_id', app.db.types.GUID(), nullable=True),
    sa.Column('recurrence_rule_id', app.db.types.GUID(), nullable=True),
    sa.Column('deleted_at', sa.Date(), nullable=True),
    sa.Column('id', app.db.types.GUID(), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
    sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
    sa.ForeignKeyConstraint(['account_id'], ['accounts.id'], ondelete='RESTRICT'),
    sa.ForeignKeyConstraint(['amortization_id'], ['amortizations.id'], ondelete='SET NULL'),
    sa.ForeignKeyConstraint(['card_installment_id'], ['credit_card_installments.id'], ondelete='SET NULL'),
    sa.ForeignKeyConstraint(['category_id'], ['categories.id'], ondelete='SET NULL'),
    sa.ForeignKeyConstraint(['commitment_installment_id'], ['commitment_installments.id'], ondelete='SET NULL'),
    sa.ForeignKeyConstraint(['invoice_id'], ['credit_card_invoices.id'], ondelete='SET NULL'),
    sa.ForeignKeyConstraint(['recurrence_rule_id'], ['recurrence_rules.id'], ondelete='SET NULL'),
    sa.ForeignKeyConstraint(['transfer_id'], ['transfers.id'], ondelete='CASCADE'),
    sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_transactions_account_id'), 'transactions', ['account_id'], unique=False)
    op.create_index(op.f('ix_transactions_amortization_id'), 'transactions', ['amortization_id'], unique=False)
    op.create_index(op.f('ix_transactions_card_installment_id'), 'transactions', ['card_installment_id'], unique=False)
    op.create_index(op.f('ix_transactions_category_id'), 'transactions', ['category_id'], unique=False)
    op.create_index(op.f('ix_transactions_commitment_installment_id'), 'transactions', ['commitment_installment_id'], unique=False)
    op.create_index(op.f('ix_transactions_competence_date'), 'transactions', ['competence_date'], unique=False)
    op.create_index(op.f('ix_transactions_invoice_id'), 'transactions', ['invoice_id'], unique=False)
    op.create_index(op.f('ix_transactions_payment_date'), 'transactions', ['payment_date'], unique=False)
    op.create_index(op.f('ix_transactions_recurrence_rule_id'), 'transactions', ['recurrence_rule_id'], unique=False)
    op.create_index(op.f('ix_transactions_status'), 'transactions', ['status'], unique=False)
    op.create_index(op.f('ix_transactions_transfer_id'), 'transactions', ['transfer_id'], unique=False)
    op.create_index(op.f('ix_transactions_type'), 'transactions', ['type'], unique=False)
    op.create_index(op.f('ix_transactions_user_id'), 'transactions', ['user_id'], unique=False)

    # Agora que 'transactions' existe, fecha os 4 FKs que apontavam "para frente".
    # batch_alter_table é necessário para que isso funcione também em SQLite, que não
    # suporta ALTER TABLE ADD CONSTRAINT diretamente (só via recriação de tabela); em
    # PostgreSQL o batch mode executa um ALTER TABLE ADD CONSTRAINT normal.
    with op.batch_alter_table('credit_card_invoices') as batch_op:
        batch_op.create_foreign_key(
            'fk_credit_card_invoices_payment_transaction_id_transactions',
            'transactions', ['payment_transaction_id'], ['id'], ondelete='SET NULL',
        )
    with op.batch_alter_table('credit_card_installments') as batch_op:
        batch_op.create_foreign_key(
            'fk_credit_card_installments_transaction_id_transactions',
            'transactions', ['transaction_id'], ['id'], ondelete='SET NULL',
        )
    with op.batch_alter_table('amortizations') as batch_op:
        batch_op.create_foreign_key(
            'fk_amortizations_transaction_id_transactions',
            'transactions', ['transaction_id'], ['id'], ondelete='SET NULL',
        )
    with op.batch_alter_table('commitment_installments') as batch_op:
        batch_op.create_foreign_key(
            'fk_commitment_installments_transaction_id_transactions',
            'transactions', ['transaction_id'], ['id'], ondelete='SET NULL',
        )

    op.create_table('amortization_installments',
    sa.Column('amortization_id', app.db.types.GUID(), nullable=False),
    sa.Column('commitment_installment_id', app.db.types.GUID(), nullable=False),
    sa.Column('id', app.db.types.GUID(), nullable=False),
    sa.ForeignKeyConstraint(['amortization_id'], ['amortizations.id'], ondelete='CASCADE'),
    sa.ForeignKeyConstraint(['commitment_installment_id'], ['commitment_installments.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('amortization_id', 'commitment_installment_id', name='uq_amortization_installment')
    )
    op.create_index(op.f('ix_amortization_installments_amortization_id'), 'amortization_installments', ['amortization_id'], unique=False)
    op.create_index(op.f('ix_amortization_installments_commitment_installment_id'), 'amortization_installments', ['commitment_installment_id'], unique=False)

    op.create_table('balance_adjustments',
    sa.Column('user_id', app.db.types.GUID(), nullable=False),
    sa.Column('account_id', app.db.types.GUID(), nullable=False),
    sa.Column('previous_balance', sa.Numeric(precision=15, scale=2), nullable=False),
    sa.Column('informed_balance', sa.Numeric(precision=15, scale=2), nullable=False),
    sa.Column('difference', sa.Numeric(precision=15, scale=2), nullable=False),
    sa.Column('date', sa.Date(), nullable=False),
    sa.Column('note', sa.Text(), nullable=True),
    sa.Column('transaction_id', app.db.types.GUID(), nullable=False),
    sa.Column('id', app.db.types.GUID(), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
    sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
    sa.ForeignKeyConstraint(['account_id'], ['accounts.id'], ondelete='CASCADE'),
    sa.ForeignKeyConstraint(['transaction_id'], ['transactions.id'], ondelete='CASCADE'),
    sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('transaction_id')
    )
    op.create_index(op.f('ix_balance_adjustments_account_id'), 'balance_adjustments', ['account_id'], unique=False)
    op.create_index(op.f('ix_balance_adjustments_user_id'), 'balance_adjustments', ['user_id'], unique=False)


def downgrade() -> None:
    op.drop_index(op.f('ix_balance_adjustments_user_id'), table_name='balance_adjustments')
    op.drop_index(op.f('ix_balance_adjustments_account_id'), table_name='balance_adjustments')
    op.drop_table('balance_adjustments')

    op.drop_index(op.f('ix_amortization_installments_commitment_installment_id'), table_name='amortization_installments')
    op.drop_index(op.f('ix_amortization_installments_amortization_id'), table_name='amortization_installments')
    op.drop_table('amortization_installments')

    with op.batch_alter_table('commitment_installments') as batch_op:
        batch_op.drop_constraint('fk_commitment_installments_transaction_id_transactions', type_='foreignkey')
    with op.batch_alter_table('amortizations') as batch_op:
        batch_op.drop_constraint('fk_amortizations_transaction_id_transactions', type_='foreignkey')
    with op.batch_alter_table('credit_card_installments') as batch_op:
        batch_op.drop_constraint('fk_credit_card_installments_transaction_id_transactions', type_='foreignkey')
    with op.batch_alter_table('credit_card_invoices') as batch_op:
        batch_op.drop_constraint('fk_credit_card_invoices_payment_transaction_id_transactions', type_='foreignkey')

    op.drop_index(op.f('ix_transactions_user_id'), table_name='transactions')
    op.drop_index(op.f('ix_transactions_type'), table_name='transactions')
    op.drop_index(op.f('ix_transactions_transfer_id'), table_name='transactions')
    op.drop_index(op.f('ix_transactions_status'), table_name='transactions')
    op.drop_index(op.f('ix_transactions_recurrence_rule_id'), table_name='transactions')
    op.drop_index(op.f('ix_transactions_payment_date'), table_name='transactions')
    op.drop_index(op.f('ix_transactions_invoice_id'), table_name='transactions')
    op.drop_index(op.f('ix_transactions_competence_date'), table_name='transactions')
    op.drop_index(op.f('ix_transactions_commitment_installment_id'), table_name='transactions')
    op.drop_index(op.f('ix_transactions_category_id'), table_name='transactions')
    op.drop_index(op.f('ix_transactions_card_installment_id'), table_name='transactions')
    op.drop_index(op.f('ix_transactions_amortization_id'), table_name='transactions')
    op.drop_index(op.f('ix_transactions_account_id'), table_name='transactions')
    op.drop_table('transactions')

    op.drop_index(op.f('ix_commitment_installments_commitment_id'), table_name='commitment_installments')
    op.drop_table('commitment_installments')

    op.drop_index(op.f('ix_amortizations_user_id'), table_name='amortizations')
    op.drop_index(op.f('ix_amortizations_commitment_id'), table_name='amortizations')
    op.drop_table('amortizations')

    op.drop_index(op.f('ix_credit_card_installments_purchase_id'), table_name='credit_card_installments')
    op.drop_index(op.f('ix_credit_card_installments_invoice_id'), table_name='credit_card_installments')
    op.drop_table('credit_card_installments')

    op.drop_index(op.f('ix_credit_card_invoices_card_id'), table_name='credit_card_invoices')
    op.drop_table('credit_card_invoices')

    op.drop_index(op.f('ix_recurrence_rules_user_id'), table_name='recurrence_rules')
    op.drop_table('recurrence_rules')

    op.drop_index(op.f('ix_budgets_user_id'), table_name='budgets')
    op.drop_index(op.f('ix_budgets_category_id'), table_name='budgets')
    op.drop_table('budgets')

    op.drop_index(op.f('ix_financial_goals_user_id'), table_name='financial_goals')
    op.drop_table('financial_goals')

    op.drop_index(op.f('ix_financial_commitments_user_id'), table_name='financial_commitments')
    op.drop_table('financial_commitments')

    op.drop_index(op.f('ix_credit_card_purchases_user_id'), table_name='credit_card_purchases')
    op.drop_index(op.f('ix_credit_card_purchases_card_id'), table_name='credit_card_purchases')
    op.drop_table('credit_card_purchases')

    op.drop_index(op.f('ix_credit_cards_user_id'), table_name='credit_cards')
    op.drop_table('credit_cards')

    op.drop_index(op.f('ix_refresh_tokens_user_id'), table_name='refresh_tokens')
    op.drop_index(op.f('ix_refresh_tokens_token_hash'), table_name='refresh_tokens')
    op.drop_table('refresh_tokens')

    op.drop_index(op.f('ix_transfers_user_id'), table_name='transfers')
    op.drop_index(op.f('ix_transfers_to_account_id'), table_name='transfers')
    op.drop_index(op.f('ix_transfers_from_account_id'), table_name='transfers')
    op.drop_table('transfers')

    op.drop_index(op.f('ix_categories_user_id'), table_name='categories')
    op.drop_index(op.f('ix_categories_parent_id'), table_name='categories')
    op.drop_table('categories')

    op.drop_index(op.f('ix_accounts_user_id'), table_name='accounts')
    op.drop_index(op.f('ix_accounts_institution_id'), table_name='accounts')
    op.drop_table('accounts')

    op.drop_index(op.f('ix_financial_institutions_user_id'), table_name='financial_institutions')
    op.drop_table('financial_institutions')

    op.drop_index(op.f('ix_users_email'), table_name='users')
    op.drop_table('users')
