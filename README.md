# NexFi — Personal Finance by Abdala Nexus

Sistema de gestão financeira pessoal: contas, cartões de crédito, financiamentos, orçamentos,
metas, recorrências e um dashboard consolidado. Construído com arquitetura pronta para evoluir
para multiusuário/SaaS (toda tabela relevante já possui `user_id`).

Documentação complementar:
- [`docs/IMPLEMENTATION_PLAN.md`](docs/IMPLEMENTATION_PLAN.md) — plano, decisões técnicas, ordem de implementação
- [`docs/DEPLOY.md`](docs/DEPLOY.md) — deploy em produção: projeto único na Vercel (frontend + API) e Neon (Postgres)
- [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md) — arquitetura, entidades, regras de negócio
- [`docs/DATABASE.md`](docs/DATABASE.md) — modelo de dados

## Stack

- **Frontend**: React 19 + TypeScript + Vite + Tailwind CSS v4 + Radix UI + TanStack Query +
  React Hook Form + Zod + Recharts + React Router.
- **Backend**: Python 3.13 + FastAPI + SQLAlchemy 2.x + Alembic + Pydantic v2 + JWT.
- **Banco de dados**: PostgreSQL (produção). O schema é dialect-agnostic e também roda em SQLite
  para desenvolvimento local sem Docker (ver decisão em `docs/IMPLEMENTATION_PLAN.md` §2.1).

## Requisitos

- Node.js 20+
- Python 3.11+
- Docker (opcional — apenas se for usar PostgreSQL via `docker-compose`)

## Atalho no Windows (`setup.bat` / `start.bat`)

- **`setup.bat`** — roda uma vez (ou sempre que atualizar o código): cria o venv do backend,
  instala dependências (backend e frontend), cria os arquivos `.env` se não existirem, aplica
  as migrations e popula o seed de desenvolvimento.
- **`start.bat`** — uso do dia a dia: só sobe o backend e o frontend em janelas separadas. Se
  detectar que algo não foi configurado (venv, `.env`, `node_modules` ou banco ausentes), avisa
  e pede para rodar `setup.bat` — não instala nem configura nada sozinho.

## Configuração

### Banco de dados

**Opção A — PostgreSQL via Docker (recomendado para uso "de verdade"):**

```bash
docker compose up -d db
```

**Opção B — SQLite (zero dependências, ótimo para avaliar o projeto rapidamente):**

Basta usar `DATABASE_URL=sqlite:///./dev.db` no `.env` do backend (é o padrão do
`.env.example`).

### Backend

```bash
cd backend
python -m venv .venv
# Windows: .venv\Scripts\activate | Linux/Mac: source .venv/bin/activate
pip install -r requirements-dev.txt   # runtime + uvicorn + pytest
cp .env.example .env
# Ajuste DATABASE_URL no .env conforme a opção escolhida acima

alembic upgrade head
python -m app.seeds.seed     # cria o usuário demo e dados de exemplo
uvicorn app.main:app --reload --port 8000
```

Documentação interativa da API: http://localhost:8000/docs

Usuário demo criado pelo seed: `demo@abdalanexus.com` / `demo123`
(configurável via `SEED_ADMIN_EMAIL` / `SEED_ADMIN_PASSWORD` no `.env`).

### Frontend

```bash
cd frontend
npm install
echo "VITE_API_URL=http://localhost:8000/api/v1" > .env
npm run dev
```

Acesse http://localhost:5173

## Testes

```bash
cd backend
pytest -v
```

Cobre as regras de negócio críticas: cálculo de saldo, transferências, rendimentos, pagamento
de fatura (sem duplicar despesa), parcelamento, pagamento de financiamento, amortização
(com desconto e rastreabilidade de parcelas), patrimônio e orçamentos.

## Build de produção (frontend)

```bash
cd frontend
npm run build   # tsc -b && vite build — gera frontend/dist
```

## Estrutura do repositório

```
nexfi/
├── backend/
│   ├── app/
│   │   ├── api/v1/        # rotas FastAPI (fino — sem regra de negócio)
│   │   ├── core/          # config, segurança (JWT/bcrypt), exceções, logging
│   │   ├── db/            # engine, sessão, tipo UUID cross-dialect
│   │   ├── models/        # SQLAlchemy ORM
│   │   ├── schemas/       # Pydantic (request/response)
│   │   ├── repositories/  # acesso a dados
│   │   ├── services/      # regras de negócio e transações
│   │   ├── seeds/         # dados de desenvolvimento
│   │   └── utils/         # dinheiro (Decimal) e datas
│   ├── alembic/           # migrations
│   └── tests/             # pytest
├── frontend/
│   └── src/
│       ├── api/           # clientes HTTP por domínio
│       ├── components/    # UI (shadcn-style) + layout + formulários
│       ├── contexts/      # auth, tema
│       ├── hooks/         # dados de referência compartilhados
│       ├── pages/         # uma página por rota
│       └── types/         # tipos TypeScript espelhando os schemas da API
├── docs/
└── docker-compose.yml
```

## Variáveis de ambiente

Ver [`backend/.env.example`](backend/.env.example). Nunca versionar `.env` real — apenas o
`.env.example`. Segredos (SECRET_KEY, credenciais de banco) devem ser gerados por ambiente.

## Funcionalidades entregues (v1)

- Autenticação JWT (access + refresh com revogação), alteração de senha, perfil.
- Instituições, contas (com saldo sempre derivado — nunca editável diretamente), categorias
  e subcategorias, transações com filtros/paginação/ordenação, transferências, ajuste de saldo
  auditável.
- Cartões de crédito: faturas com fechamento/vencimento automáticos, compras parceladas com
  rateio de centavos, pagamento de fatura sem duplicar despesa.
- Financiamentos: cronograma de parcelas, pagamento, amortização extraordinária (redução de
  prazo ou de parcela) com cálculo de desconto e rastreabilidade total das parcelas afetadas.
- Planejamento: orçamentos (padrão ou por mês específico, somando subcategorias), metas
  financeiras (com progresso vinculável a uma conta), recorrências (geração de transações
  futuras com horizonte configurável, idempotente).
- Dashboard: indicadores consolidados, contas, cartões, financiamentos, gráficos (receitas x
  despesas, despesas por categoria, evolução patrimonial, rendimentos), projeção de saldo.
- Suporte a tema claro/escuro, formatação 100% pt-BR (moeda, datas, percentuais).

## Limitações conhecidas / próximos passos

- "Evolução patrimonial" reconstrói o saldo devedor histórico dos financiamentos a partir do
  cronograma de parcelas; para `REDUCAO_PARCELA`, usa o valor original da parcela como
  aproximação para datas passadas (documentado em `docs/ARCHITECTURE.md`).
- Sem integração bancária, Open Finance, Pix, boletos, upload de comprovantes, OCR ou IA —
  intencionalmente fora do escopo do MVP (ver `docs/IMPLEMENTATION_PLAN.md` §6).
