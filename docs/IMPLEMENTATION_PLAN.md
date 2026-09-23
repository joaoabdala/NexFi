# NexFi — Plano de Implementação (v1)

> Documento vivo. Atualizado conforme decisões técnicas são tomadas durante a implementação.

## 1. Visão Geral

NexFi é um sistema de gestão financeira pessoal, construído desde já com arquitetura multiusuário
(toda tabela relevante possui `user_id`), mesmo operando no MVP com um único usuário seed.

Monorepo:

```
nexfi/
├── backend/   # FastAPI + SQLAlchemy 2.x + Alembic + PostgreSQL
├── frontend/  # React + TypeScript + Vite + Tailwind + shadcn/ui
├── docs/
├── docker-compose.yml
└── README.md
```

## 2. Arquitetura Backend

```
API (FastAPI routers)
    ↓ (Pydantic schemas: request/response)
Services (regras de negócio, orquestração, transações de banco)
    ↓
Repositories (acesso a dados via SQLAlchemy, sem regra de negócio)
    ↓
Models (SQLAlchemy ORM) / PostgreSQL
```

- Rotas nunca acessam `Session`/repositórios diretamente para regra de negócio — apenas
  validam entrada (via Pydantic), chamam o service correspondente e serializam saída.
- Services levantam exceções de domínio (`app/core/exceptions.py`) traduzidas para HTTP no
  nível da API via exception handlers globais — nenhuma rota faz `try/except HTTPException` manual
  espalhado.
- Toda operação multi-tabela crítica (transferência, pagamento de fatura, criação de compra
  parcelada, pagamento de financiamento, amortização, ajuste de saldo) roda dentro de uma
  única transação (`session.begin()`), com rollback automático em qualquer exceção.
- Saldo de conta é **sempre derivado** (nunca um campo editável diretamente):
  `saldo_atual = saldo_inicial + soma(transações CONFIRMADA que afetam a conta)`.
  Isso é calculado por uma projeção (view/consulta agregada), não por um job que reescreve o
  campo — evita divergência.

### 2.1 Decisão técnica: portabilidade de dialeto (Postgres/SQLite)

PostgreSQL é o banco de destino documentado e usado em produção (`docker-compose.yml`).
Como o ambiente de desenvolvimento onde este código foi gerado não possui Docker/Postgres
disponíveis, o schema foi desenhado para ser **dialect-agnostic**:

- UUID: `TypeDecorator` próprio (`app/db/types.py::GUID`) — usa `UUID` nativo no Postgres e
  `CHAR(32)` no SQLite. Chave primária de toda tabela.
- Enums: armazenados como `VARCHAR` com `CHECK CONSTRAINT` (`sa.Enum(..., native_enum=False)`),
  nunca `ENUM` nativo do Postgres — evita quebra de `alembic upgrade` em SQLite e simplifica
  futuras adições de valores (não exige `ALTER TYPE`).
  Isso permite rodar toda a suíte de testes e um smoke-test de migração/seed com SQLite,
  mantendo Postgres como alvo real via `DATABASE_URL`.
- Dinheiro: `NUMERIC(15,2)` em ambos os dialetos, sempre manipulado como `Decimal` no Python
  (nunca `float`).

## 3. Modelo de Dados

Convenções: toda tabela tem `id UUID PK`, `created_at`, `updated_at` (timestamptz,
`America/Sao_Paulo` como timezone de aplicação, armazenado em UTC). Soft delete (`deleted_at`)
onde aplicável; senão status `CANCELADA`/`ativo`.

### Entidades principais

- **users** — autenticação (email, password_hash, nome, timezone, locale, is_active).
- **financial_institutions** (user_id, nome, nome_curto, ativo, observação)
- **accounts** (user_id, institution_id, nome, tipo, saldo_inicial, data_saldo_inicial, ativa,
  incluir_patrimonio_disponivel, incluir_patrimonio_investido, observação)
- **categories** (user_id, nome, tipo[RECEITA/DESPESA/AMBOS], parent_id nullable → subcategoria,
  ativa)
- **transactions** (user_id, account_id, category_id, tipo[RECEITA/DESPESA/TRANSFERENCIA/
  RENDIMENTO/AJUSTE], descrição, valor NUMERIC positivo + sinal implícito pelo tipo,
  data_competencia, data_pagamento, status[PENDENTE/CONFIRMADA/CANCELADA], origem,
  referência_externa, transfer_id nullable, card_purchase_installment_id nullable,
  commitment_installment_id nullable, recurrence_rule_id nullable)
  - `tipo` extensível: coluna string, não enum nativo do banco.
- **transfers** (user_id, from_account_id, to_account_id, valor, data, descrição) — 1 registro
  lógico; gera 2 `transactions` tipo TRANSFERENCIA vinculadas por `transfer_id`, nunca afeta
  receita/despesa.
- **balance_adjustments** (user_id, account_id, valor_anterior, valor_informado, diferença,
  data, observação, transaction_id) — a transação gerada é tipo AJUSTE.
- **credit_cards** (user_id, institution_id, nome, bandeira, últimos_4, limite, dia_fechamento,
  dia_vencimento, conta_pagamento_padrao_id, ativo)
- **credit_card_invoices** (card_id, competência[ano-mês], data_fechamento, data_vencimento,
  status[ABERTA/FECHADA/PAGA], valor_calculado, data_pagamento, conta_pagamento_id)
- **credit_card_purchases** (card_id, descrição, valor_total, parcelas_total, data_compra,
  categoria_id) — compra "guarda-chuva"
- **credit_card_installments** (purchase_id, invoice_id, número, valor, transaction_id) — cada
  parcela gera 1 transaction tipo DESPESA vinculada; pagamento da fatura NÃO gera nova DESPESA,
  gera uma transaction tipo `TRANSFERENCIA`-like específica (`FATURA_PAGAMENTO`, ver §2 regra
  crítica) que apenas debita a conta.
- **financial_commitments** (generaliza financiamento/empréstimo/consórcio): user_id,
  institution_id, tipo, nome, valor_bem, entrada, valor_financiado, taxa_juros, parcelas_total,
  valor_parcela_padrao, data_inicial, dia_vencimento, saldo_devedor_atual, status, observação
- **commitment_installments** (commitment_id, número, vencimento, valor_original,
  valor_atualizado, valor_pago, data_pagamento, status[PENDENTE/PAGA/AMORTIZADA/CANCELADA],
  transaction_id nullable, amortization_id nullable)
- **amortizations** (commitment_id, data, valor_pago, valor_nominal_amortizado,
  desconto_obtido[computed], tipo[REDUCAO_PRAZO/REDUCAO_PARCELA], conta_id, observação,
  transaction_id)
- **amortization_installments** (amortization_id, commitment_installment_id) — tabela de
  associação N:N explícita para rastreabilidade total de quais parcelas cada amortização afetou.
- **budgets** (user_id, category_id, valor, mês nullable=regra recorrente padrão,
  ano nullable, is_default) — orçamento padrão (mês/ano nulos) vs específico de um mês.
- **financial_goals** (user_id, nome, valor_alvo, valor_atual, conta_vinculada_id nullable,
  data_alvo, status)
- **recurrence_rules** (user_id, descrição, tipo[RECEITA/DESPESA], valor, categoria_id,
  conta_id, frequência[SEMANAL/MENSAL/ANUAL/PERSONALIZADA], dia_referência, data_inicio,
  data_fim nullable, ativo) — job gera transações PENDENTE alguns meses à frente
  (`RECURRENCE_HORIZON_MONTHS`, padrão 3), idempotente por `(rule_id, competência)`.
- **refresh_tokens** (user_id, token_hash, expires_at, revoked_at) — suporte a refresh JWT.

### Relacionamentos-chave

- `transaction.account_id` sempre aponta para a conta afetada (mesmo em parcelas de cartão —
  nesse caso não afeta saldo de conta diretamente até o pagamento da fatura; ver regra abaixo).
- Regra da fatura: compras no cartão geram `transactions` tipo DESPESA com `account_id = NULL`
  e `card_purchase_installment_id` preenchido — contam para indicadores de despesa por
  competência mas não debitam conta nenhuma. O pagamento da fatura gera 1 transação tipo
  `AJUSTE`... **decisão**: criar tipo `TRANSFERENCIA` interno especial não é adequado (não há
  conta destino real de "fatura"). Optou-se por um tipo próprio `PAGAMENTO_FATURA` que debita
  `conta_pagamento_id` e é explicitamente excluído do somatório de despesas do dashboard,
  aparecendo apenas como movimentação de caixa.

## 4. Ordem de Implementação

1. Plano (este documento) — ✅
2. Monorepo + docker-compose + README esqueleto
3. Backend core (config, db session, security/JWT, exception handling)
4. Models completos + Alembic migração inicial
5. Auth (login/logout/refresh/change-password) + seed de usuário admin
6. Núcleo financeiro: instituições, contas (+ saldo derivado), categorias, transações,
   transferências, ajuste de saldo
7. Cartões: cadastro, faturas, compras parceladas, pagamento de fatura
8. Financiamentos: cadastro, parcelas, pagamento, amortização
9. Planejamento: orçamentos, metas, recorrências (+ geração de transações futuras)
10. Dashboard: agregações (saldo, patrimônio, gráficos, projeção)
11. Seeds de desenvolvimento
12. Testes pytest das regras críticas
13. Frontend: scaffold, tema, layout, auth
14. Frontend: Dashboard
15. Frontend: Transações
16. Frontend: Financeiro (contas/cartões/financiamentos/rendimentos)
17. Frontend: Planejamento + Configurações
18. Validação final (build, testes, migrations, docs)

## 5. Decisões Técnicas Registradas

| Decisão | Motivo |
|---|---|
| UUID via TypeDecorator cross-dialect | Permite testar sem Postgres local; produção usa Postgres nativo |
| Enums como VARCHAR + CHECK, não ENUM nativo | Evita `ALTER TYPE` em migrações futuras; portável |
| Saldo de conta derivado, nunca campo editável | Requisito explícito da especificação (§10) |
| Fatura paga não gera nova despesa | Requisito crítico da especificação (§22) — tipo de transação dedicado `PAGAMENTO_FATURA` |
| Transferência = 1 registro `transfers` + 2 `transactions` vinculadas por `transfer_id` | Garante rastreabilidade e impede transações "órfãs" |
| Amortização com tabela de associação N:N para parcelas afetadas | Requisito de rastreabilidade total (§29) |
| JWT access curto (15 min) + refresh token opaco em tabela própria, hash armazenado | Padrão seguro, permite revogação |
| Geração de recorrências limitada a N meses à frente (idempotente) | Evita explosão de linhas (§33) |
| API versionada em `/api/v1` | Requisito §41 |
| Frontend não implementa Next.js; SPA Vite + React Router | Requisito explícito |

## 6. Fora de Escopo do MVP (ver §58 do briefing)

Open Finance, integrações bancárias automáticas, Pix, boletos, upload de comprovantes, OCR, IA,
investimentos complexos, múltiplas moedas, emissão fiscal. Arquitetura não impede evolução futura.
