# NexFi — Modelo de Dados

PostgreSQL (produção) via SQLAlchemy 2.x + Alembic. Convenções globais:

- **PK**: `id UUID`, gerado no aplicativo (`uuid4`), tipo `GUID` (`app/db/types.py`) — nativo
  `UUID` no Postgres, `CHAR(32)` no SQLite (só usado localmente sem Docker).
- **Timestamps**: `created_at` / `updated_at` (`timestamptz`, preenchidos automaticamente).
- **Dinheiro**: sempre `NUMERIC(15,2)`, nunca `FLOAT`; manipulado como `Decimal` em Python.
- **Enums**: `VARCHAR` + `CHECK CONSTRAINT` (`native_enum=False`) em vez de `ENUM` nativo do
  Postgres — evita `ALTER TYPE` ao adicionar valores no futuro e mantém migrations portáveis.
- **Multiusuário desde já**: toda tabela de domínio tem `user_id`, mesmo com um único usuário
  seed hoje.

## Tabelas

### `users`
`email` (único), `password_hash`, `name`, `timezone`, `locale`, `is_active`, `role` (enum
`UserRole`: `ADMIN`/`USER`, padrão `USER` — controla acesso ao painel de administração).

### `refresh_tokens`
`user_id` → users, `token_hash` (único, SHA-256 do token opaco), `expires_at`, `revoked_at`.

### `financial_institutions`
`user_id`, `name`, `short_name`, `active`, `note`.

### `accounts`
`user_id`, `institution_id` → financial_institutions, `name`, `type` (enum `AccountType`),
`initial_balance`, `initial_balance_date`, `active`, `include_in_available_worth`,
`include_in_invested_worth`, `note`, `deleted_at`.
Saldo atual **não é uma coluna** — é sempre calculado (ver ARCHITECTURE.md).

### `categories`
`user_id`, `parent_id` → categories (self-FK, subcategoria), `name`, `kind` (RECEITA/DESPESA/
AMBOS), `active`. Apenas um nível de subcategoria é permitido (validado em `category_service`).

### `transactions`
Tabela central. `user_id`, `account_id` (nullable — nulo para despesas de cartão ainda não
faturadas/pagas), `category_id`, `description`, `type` (enum `TransactionType`: RECEITA,
DESPESA, TRANSFERENCIA, RENDIMENTO, AJUSTE, PAGAMENTO_FATURA, PAGAMENTO_FINANCIAMENTO,
AMORTIZACAO — extensível, string livre com CHECK), `amount`, `competence_date`, `payment_date`,
`status` (PENDENTE/CONFIRMADA/CANCELADA), `note`, `origin` (MANUAL/TRANSFERENCIA/CARTAO/
FINANCIAMENTO/AMORTIZACAO/AJUSTE_SALDO/PAGAMENTO_FATURA/RECORRENCIA), `external_reference`,
`deleted_at`, e FKs opcionais de rastreabilidade: `transfer_id`, `card_installment_id`,
`invoice_id`, `commitment_installment_id`, `amortization_id`, `recurrence_rule_id`.

### `transfers`
`user_id`, `from_account_id`, `to_account_id`, `amount`, `date`, `description`, `note`.
Gera exatamente 2 `transactions` (tipo TRANSFERENCIA) vinculadas por `transfer_id`.

### `balance_adjustments`
`user_id`, `account_id`, `previous_balance`, `informed_balance`, `difference`, `date`, `note`,
`transaction_id` (único — 1:1 com a transação tipo AJUSTE gerada).

### `credit_cards`
`user_id`, `institution_id`, `name`, `brand`, `last_digits`, `credit_limit`, `closing_day`,
`due_day`, `default_payment_account_id` → accounts, `active`.

### `credit_card_invoices`
`card_id`, `competence` (primeiro dia do mês), `closing_date`, `due_date`, `status` (ABERTA/
FECHADA/PAGA/VENCIDA — recalculado sob demanda a partir das datas), `payment_date`,
`payment_account_id`, `payment_transaction_id`. Único por `(card_id, competence)`.
`amount` **não é armazenado** — sempre computado como a soma das parcelas vinculadas.

### `credit_card_purchases`
`user_id`, `card_id`, `category_id`, `description`, `total_amount`, `installments_total`,
`purchase_date`. É a compra "guarda-chuva"; o rateio de centavos entre parcelas é feito em
`app/utils/money.py::split_installments` (resíduo vai para a última parcela).

### `credit_card_installments`
`purchase_id`, `invoice_id`, `number`, `amount`, `transaction_id`. Único por
`(purchase_id, number)`. Cada linha gera exatamente uma `transaction` tipo DESPESA.

### `financial_commitments`
Generaliza financiamento/empréstimo/consórcio (conceito interno *Financial Commitment*, para
evoluir sem redesenho). `user_id`, `institution_id`, `type`, `name`, `asset_value`,
`down_payment`, `financed_amount`, `interest_rate`, `installments_total`,
`default_installment_amount`, `start_date`, `due_day`, `outstanding_balance` (recalculado, nunca
ajustado incrementalmente), `status` (ATIVO/QUITADO/CANCELADO), `note`.

### `commitment_installments`
`commitment_id`, `number`, `due_date`, `original_amount`, `updated_amount` (reduzido por
amortizações tipo REDUCAO_PARCELA), `paid_amount`, `payment_date`, `status` (PENDENTE/PAGA/
AMORTIZADA/CANCELADA), `transaction_id`, `amortization_id`. Único por `(commitment_id, number)`.

### `amortizations`
`user_id`, `commitment_id`, `date`, `paid_amount`, `nominal_amortized_amount`,
`discount_obtained` (= nominal − pago, calculado no servidor), `type` (REDUCAO_PRAZO/
REDUCAO_PARCELA), `account_id`, `note`, `transaction_id`.

### `amortization_installments`
Associação N:N explícita entre `amortizations` e `commitment_installments` — existe
especificamente para que cada amortização saiba, de forma consultável e auditável, exatamente
quais parcelas afetou (requisito de rastreabilidade total). Único por
`(amortization_id, commitment_installment_id)`.

### `budgets`
`user_id`, `category_id`, `amount`, `month`/`year` (ambos nulos = orçamento padrão recorrente;
ambos preenchidos = sobrescreve o padrão naquele mês específico), `is_default`. Único por
`(user_id, category_id, month, year)`. O "realizado" no resumo soma a categoria e todas as suas
subcategorias.

### `financial_goals`
`user_id`, `name`, `target_amount`, `current_amount`, `linked_account_id` (opcional — quando
presente, o progresso passa a ser o saldo real da conta, não o valor manual), `target_date`,
`status` (EM_ANDAMENTO/CONCLUIDA/CANCELADA).

### `recurrence_rules`
`user_id`, `description`, `type` (RECEITA/DESPESA), `amount`, `category_id`, `account_id`,
`frequency` (SEMANAL/MENSAL/ANUAL/PERSONALIZADA), `reference_day`, `custom_interval_days`,
`start_date`, `end_date`, `active`, `last_generated_competence` (cursor de geração idempotente).

## Diagrama de relacionamento (simplificado)

```
users 1—N financial_institutions, accounts, categories, transactions, credit_cards,
           financial_commitments, budgets, financial_goals, recurrence_rules

financial_institutions 1—N accounts, credit_cards, financial_commitments

accounts 1—N transactions (account_id)
accounts 1—1 balance_adjustments (via transaction_id)

categories 1—N categories (parent_id, 1 nível de subcategoria)
categories 1—N transactions, budgets

transfers 1—N transactions (transfer_id, exatamente 2)

credit_cards 1—N credit_card_invoices, credit_card_purchases
credit_card_purchases 1—N credit_card_installments
credit_card_invoices 1—N credit_card_installments
credit_card_installments 1—1 transactions (transaction_id)

financial_commitments 1—N commitment_installments, amortizations
amortizations N—N commitment_installments (via amortization_installments)
```

## Migrations

Geradas com Alembic (`alembic revision --autogenerate`). A migration inicial
(`75952d1bc0b4_initial_schema.py`) cria todas as 19 tabelas, índices e constraints. O template
(`alembic/script.py.mako`) importa `app.db.types` automaticamente para que o tipo `GUID`
customizado seja resolvido em migrations futuras sem edição manual.

**Ordem de criação e FKs circulares.** `transactions`, `credit_card_invoices`,
`credit_card_installments`, `amortizations` e `commitment_installments` formam um ciclo genuíno
de dependência (cada um tem uma coluna nullable `SET NULL` apontando de volta para
`transactions`). A migration inicial cria as tabelas em ordem topológica válida e só fecha esses
4 FKs "de volta" via `ALTER TABLE` (dentro de `op.batch_alter_table`, para funcionar também em
SQLite) depois que `transactions` já existe. Isso importa porque SQLite não valida a ordem de
criação de FKs — um autogenerate ingênuo funciona "por acaso" em SQLite mas quebra em
PostgreSQL real, que exige que a tabela referenciada já exista no momento do `CREATE TABLE`.
A migration `877dd7756903_add_user_role.py` adiciona `users.role` com `server_default='USER'`
(backfill automático de linhas existentes) e promove o e-mail configurado em
`SEED_ADMIN_EMAIL` a `ADMIN`.
