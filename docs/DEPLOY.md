# Deploy — Vercel + Neon

Arquitetura de produção:

```
navegador ──► nexfi (Vercel, projeto "frontend")      estático via CDN
         └──► nexfi-api (Vercel, projeto "backend")    FastAPI como Vercel Function (gru1)
                     └──► Neon Postgres (sa-east-1)    via pooler (PgBouncer)
```

São **dois projetos Vercel apontando para o mesmo repositório**, cada um com seu Root Directory.
Frontend e API ficam em domínios diferentes, por isso o CORS é configurado na API (com cache de
preflight de 24h, para não pagar um OPTIONS extra a cada chamada).

> Por que não Vercel Services (um projeto só, mesmo domínio)? Ainda está em beta e exige
> permissão na conta. Quando virar GA, dá para migrar sem mudar código — só configuração.

## 1. Neon

1. Criar projeto na região **AWS São Paulo (sa-east-1)** — a mesma região das funções (`gru1`).
2. Em *Compute*, manter o tamanho **mínimo (0,25 CU)**: o Free tem 100 CU-horas/mês.
3. Copiar a connection string **pooled** (host com `-pooler`). Formato:
   `postgresql://usuario:senha@ep-xxx-pooler.sa-east-1.aws.neon.tech/neondb?sslmode=require&channel_binding=require`
   - Pode colar como está: a API troca `postgresql://` por `postgresql+psycopg://` sozinha.
   - **Nunca** versionar essa string nem colá-la em chats/issues.

## 2. Migrations e primeiro usuário (rodar da sua máquina)

As migrations **não** rodam no deploy (evita que um preview deployment altere o banco de
produção). Rodam manualmente, apontando para o Neon:

```bash
cd backend
# No .env: DATABASE_URL=<connection string do Neon>
.venv\Scripts\alembic upgrade head
.venv\Scripts\python -m app.seeds.create_admin   # pede e-mail, nome e senha no terminal
# Depois, volte o .env para sqlite:///./dev.db se quiser continuar desenvolvendo localmente
```

> **Não** rode `python -m app.seeds.seed` no Neon: ele cria o usuário demo com dados fictícios.

## 3. Projeto Vercel — backend

- **Import** do repositório `joaoabdala/NexFi` → Root Directory: **`backend`**.
- Framework: detectado como **FastAPI** (entrypoint `app/main.py`, Python via `.python-version`).
- Região e limites já vêm do `backend/vercel.json` (`gru1`, 30 s).
- **Environment Variables** (Production):

| Variável | Valor |
|---|---|
| `DATABASE_URL` | connection string pooled do Neon |
| `SECRET_KEY` | aleatória, 64+ caracteres — gerar com `python -c "import secrets; print(secrets.token_urlsafe(64))"` |
| `ENVIRONMENT` | `production` (a API se recusa a subir com a SECRET_KEY padrão) |
| `CORS_ORIGINS` | URL do frontend, ex.: `https://nexfi.vercel.app` |
| `CORS_ORIGIN_REGEX` | *(opcional)* para liberar previews, ex.: `https://nexfi-[a-z0-9-]+\.vercel\.app` |

Depois do deploy, conferir `https://<backend>.vercel.app/health` → `{"status":"ok"}`.

## 4. Projeto Vercel — frontend

- **Import** do mesmo repositório → Root Directory: **`frontend`**.
- Framework: detectado como **Vite** (build `npm run build`, saída `dist`).
- `frontend/vercel.json` já faz o fallback de rotas da SPA para `index.html` e cache longo de `/assets`.
- **Environment Variables**:

| Variável | Valor |
|---|---|
| `VITE_API_URL` | `https://<backend>.vercel.app/api/v1` |

> `VITE_API_URL` é embutida no bundle em tempo de build: ao alterá-la, faça **Redeploy**.

## 5. Ordem recomendada

1. Neon criado → migrations + `create_admin` (passo 2).
2. Deploy do backend → anotar a URL.
3. Deploy do frontend com `VITE_API_URL` → anotar a URL.
4. Voltar no backend: `CORS_ORIGINS` = URL do frontend → **Redeploy** do backend.

## Comportamentos esperados no plano Free

- **Primeiro acesso após inatividade é mais lento** (~1–2 s): o Neon suspende o compute após
  5 min parado e a função Python também tem cold start. Os acessos seguintes são normais.
- Storage do Neon Free: 0,5 GB — sobra para anos de uso pessoal (uma transação ocupa ~0,5–1 KB
  com índices; 300 lançamentos/mês ≈ 5–10 MB/ano). Tokens de sessão antigos são apagados
  automaticamente a cada login/refresh. Ao passar de 0,5 GB o Neon bloqueia escritas.
