# NexFi — Arquitetura

## Visão geral

Monorepo com backend (FastAPI) e frontend (React SPA) desacoplados, comunicando-se via
REST versionado em `/api/v1`. Ver [`IMPLEMENTATION_PLAN.md`](IMPLEMENTATION_PLAN.md) para as
decisões técnicas registradas durante a implementação.

## Backend — camadas

```
API (app/api/v1/*)         — valida entrada (Pydantic), chama service, serializa saída
    ↓
Services (app/services/*)  — regra de negócio, orquestração, transações de banco
    ↓
Repositories (app/repositories/*) — consultas SQLAlchemy, sem regra de negócio
    ↓
Models (app/models/*) / PostgreSQL
```

Erros de domínio são exceções tipadas (`app/core/exceptions.py`: `NotFoundError`,
`ValidationError`, `ConflictError`, `UnauthorizedError`, `ForbiddenError`) capturadas por
exception handlers globais em `app/main.py`, que as traduzem para o status HTTP correto —
nenhuma rota faz tratamento de erro ad-hoc.

Toda consulta de repositório recebe `user_id` e filtra por ele — não existe endpoint que
retorne dados de outro usuário (verificado nos testes e reforçado pelo padrão de todas as
funções `get_by_id(db, user_id, id)`).

## Autenticação

JWT de acesso de vida curta (15 min por padrão) + refresh token opaco (alta entropia,
armazenado com hash SHA-256 em `refresh_tokens`, nunca em texto puro). O refresh é rotacionado
a cada uso (o antigo é revogado). Senhas com bcrypt (via passlib). O frontend intercepta 401,
tenta um refresh único e reenfileira a requisição original; se o refresh falhar, redireciona
para `/login`.

## Papéis de usuário e administração

`users.role` (`ADMIN`/`USER`, padrão `USER`) habilita um painel de administração
(`/api/v1/admin/users`, tela `/admin/usuarios` no frontend) restrito a administradores via a
dependência `get_current_admin_user` (`app/api/deps.py`) — retorna 403 para não-admins. O
usuário demo criado pelo seed é `ADMIN` (backfill também aplicado por migration para bancos já
existentes). No frontend, o link só aparece no sidebar para `role === "ADMIN"`
(`components/layout/Sidebar.tsx`) e a rota é protegida por `AdminRoute`, que redireciona
não-admins para o Dashboard — dupla proteção (rota + link), já que o backend é a fonte de
verdade real de autorização.

Regras de segurança em `admin_user_service.py`: um admin não pode excluir a própria conta, e o
último administrador ativo do sistema não pode ser excluído, desativado nem rebaixado (evita
perda total de acesso administrativo). Excluir um usuário é uma operação em cascata real — todas
as instituições, contas, transações, cartões, financiamentos etc. desse usuário são removidos
junto (`ON DELETE CASCADE` no banco). Para que isso também funcione em SQLite (usado sem Docker),
a sessão habilita `PRAGMA foreign_keys=ON` por conexão (`app/db/session.py`), já que o SQLite não
aplica FKs por padrão.

## Regra de saldo (núcleo do sistema)

Saldo de conta **nunca é um campo editável**. É sempre derivado:

```
saldo_atual = saldo_inicial + Σ(transações CONFIRMADA que afetam a conta)
```

Implementado em `app/services/balance_service.py::get_account_balance`, que soma a
contribuição assinada de cada transação confirmada vinculada à conta:

| Tipo | Contribuição |
|---|---|
| RECEITA, RENDIMENTO | `+valor` |
| DESPESA, PAGAMENTO_FATURA, PAGAMENTO_FINANCIAMENTO, AMORTIZACAO | `-valor` |
| AJUSTE | `+valor` (o valor já é a diferença assinada, pode ser negativa) |
| TRANSFERENCIA | `-valor` se a conta é a origem do `Transfer`, `+valor` se é o destino |

Ajuste de saldo (`account_service.create_balance_adjustment`) calcula a diferença entre o saldo
informado e o saldo calculado, e grava essa diferença como uma transação tipo `AJUSTE` — nunca
sobrescreve o saldo diretamente, preservando auditoria total.

## Transferências

Uma transferência é 1 registro `Transfer` + 2 `Transaction` (tipo `TRANSFERENCIA`) vinculadas
por `transfer_id`, criados atomicamente (`transfer_service.create_transfer`, com rollback em
qualquer falha). Nunca gera receita/despesa e nunca altera o patrimônio total do usuário.

## Cartões, faturas e a regra crítica de pagamento

- Uma compra no cartão (`purchase_service.create_purchase`) já gera `N` transações tipo
  `DESPESA` (uma por parcela, `account_id = NULL`) no momento da compra — a despesa é
  reconhecida por competência, independente de quando o dinheiro efetivamente sai da conta.
- Cada fatura (`CreditCardInvoice`) é criada sob demanda (`invoice_service.get_or_create_invoice`)
  quando a primeira parcela cai nela; seu valor é sempre **calculado** a partir da soma das
  parcelas vinculadas, nunca armazenado como número solto.
- **Pagar a fatura não gera uma nova despesa.** `invoice_service.pay_invoice` cria uma
  transação de tipo próprio `PAGAMENTO_FATURA`, que debita a conta de pagamento mas é
  explicitamente excluída do somatório de despesas do dashboard (`dashboard_service` só soma
  `TransactionType.DESPESA`). Isso é coberto por teste (`tests/test_invoice_payment.py`).
- O limite disponível de um cartão é `limite - Σ(valor das faturas não pagas)`, incluindo
  faturas futuras já geradas pelas parcelas — reflete o comportamento real de bancos
  brasileiros, que reservam o valor total do parcelamento contra o limite no momento da compra.

## Financiamentos e amortização

- `financing_service.create_commitment` gera o cronograma completo de parcelas
  (`CommitmentInstallment`) no momento da criação, com `due_day` mensal a partir de `start_date`.
- `outstanding_balance` do financiamento é **recalculado** (nunca ajustado incrementalmente) como
  a soma de `updated_amount` de todas as parcelas `PENDENTE` (`_recompute_outstanding_balance`),
  eliminando qualquer risco de divergência entre pagamentos e amortizações.
- Amortização (`create_amortization`):
  - `REDUCAO_PRAZO`: as parcelas selecionadas (devem ser informadas explicitamente) mudam de
    `PENDENTE` para `AMORTIZADA` — são eliminadas do cronograma, mas continuam existindo como
    registro histórico, vinculadas à amortização via `AmortizationInstallment` (associação N:N
    explícita, garantindo rastreabilidade total de quais parcelas cada amortização afetou).
  - `REDUCAO_PARCELA`: as parcelas continuam `PENDENTE`, mas seu `updated_amount` é reduzido
    proporcionalmente ao desconto obtido — o prazo não muda, o valor de cada parcela futura sim.
  - `discount_obtained = nominal_amortized_amount - paid_amount`, sempre calculado no servidor
    (nunca aceito do cliente), com base na soma do `updated_amount` das parcelas afetadas.

## Dashboard e patrimônio

- Patrimônio bruto = soma do saldo de todas as contas com `include_in_available_worth` ou
  `include_in_invested_worth`. Patrimônio líquido = bruto − saldo devedor de financiamentos.
- Para os gráficos de evolução (patrimônio, rendimentos, receitas x despesas), o histórico é
  reconstruído por competência a partir das transações confirmadas até a data de referência —
  não há snapshots armazenados. Para o saldo devedor histórico dos financiamentos, uma parcela
  só deixa de compor a dívida quando sua baixa (pagamento ou amortização) já ocorreu até aquela
  data; para simplificar, usa-se o valor original da parcela nesse cálculo retroativo (uma
  redistribuição de `REDUCAO_PARCELA` não é "desfeita" mês a mês no gráfico — é uma aproximação
  aceitável para uma visualização, documentada aqui).
- "Regime de caixa" (padrão do MVP, conforme especificação) é aproximado usando
  `competence_date` para os agregados mensais, já que compras no cartão só têm data de
  competência no momento em que a despesa é reconhecida (o evento de caixa real é o pagamento
  da fatura, tratado separadamente como `PAGAMENTO_FATURA` e explicitamente fora do somatório de
  despesas).

## Recorrências

`recurrence_service.generate_pending_transactions` gera transações `PENDENTE` a partir de
`last_generated_competence` (ou `start_date`, na primeira execução) até um horizonte de
`RECURRENCE_HORIZON_MONTHS` (padrão 3) meses à frente, avançando o cursor da regra a cada
execução — idempotente por construção (nunca gera a mesma competência duas vezes). É invocado
automaticamente ao listar recorrências e também exposto via `POST /recurrences/generate` para
disparo manual.

## Frontend

SPA em React Router (sem Next.js, por requisito). Camadas:

- `api/*` — funções finas de acesso HTTP por domínio (axios), tipadas.
- `hooks/useReferenceData.ts` — dados compartilhados entre formulários (contas, categorias,
  instituições) via TanStack Query, evitando refetch duplicado.
- `components/ui/*` — primitivos de UI no estilo shadcn (Radix + Tailwind + CVA), escritos à
  mão (sem CLI) para casar exatamente com os tokens de marca da Abdala Nexus.
- `components/forms/*` — um diálogo por operação de escrita (criar/editar conta, compra no
  cartão, amortização etc.), cada um com seu próprio `react-hook-form` + `zod`.
- `pages/*` — uma página por rota, compõe hooks de dados + componentes de UI; não contém lógica
  de negócio (cálculos financeiros são sempre responsabilidade do backend).
- Tema claro/escuro via atributo `data-theme` na raiz do documento + variáveis CSS
  (`prefers-color-scheme` como padrão quando não há preferência explícita salva).

## Segurança

- CORS restrito às origens configuradas em `CORS_ORIGINS`.
- Toda rota (exceto `/auth/login`, `/auth/refresh`, `/health`) exige um JWT válido via
  `Depends(get_current_user)`.
- Toda consulta de dados é filtrada por `user_id` — nunca por um identificador vindo do cliente
  sem verificação de posse.
- Exceções não tratadas nunca vazam stack trace/detalhes internos ao cliente (handler global
  genérico retorna 500 com mensagem fixa; o detalhe vai para o log do servidor).
