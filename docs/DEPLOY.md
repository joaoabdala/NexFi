# Deploy — Vercel + Neon

Arquitetura de produção — **um único projeto Vercel**, frontend e API no mesmo domínio:

```
navegador ──► nexfi.abdalanexus.com (Cloudflare → Vercel)
               ├─ /, /assets/*        → função (build do React em backend/public/), cacheado na Cloudflare
               ├─ /api/v1/*           → FastAPI (Vercel Function, região gru1)
               └─ /transacoes, ...    → FastAPI devolve o index.html (F5 em rota do React)
                        │
                        └──► Neon Postgres (sa-east-1), via pooler (PgBouncer)
```

Como funciona:

- O projeto Vercel tem Root Directory `backend` e é detectado como **FastAPI** (`app/main.py`).
- O `buildCommand` de [`backend/vercel.json`](../backend/vercel.json) compila o frontend
  (`frontend/`) e copia o `dist/` para `backend/public/`, que entra no pacote da função
  (`includeFiles: public/**`). A rota `spa_fallback` (`app/main.py`) serve esses arquivos — os
  de `/assets` com cache imutável — e devolve o `index.html` para rotas do React (F5, link
  compartilhado). **A Vercel não promove ao CDN um `public/` gerado no build** (confirmado no
  1º deploy: os assets davam 404 e a tela ficava preta); quem cacheia os assets é a Cloudflare.
- Erros (404) saem com `Cache-Control: no-store`. Se algum dia um erro ficar em cache na
  Cloudflare (tela preta com o HTML carregando), limpe: Cloudflare → abdalanexus.com → Caching →
  Configuration → **Purge Everything**, e Ctrl+Shift+R no navegador.
- O build de produção usa [`frontend/.env.production`](../frontend/.env.production)
  (`VITE_API_URL=/api/v1`): mesma origem, **sem CORS** e sem preflight.

> Alternativa descartada por ora: Vercel Services (beta, exige permissão na conta).

## 1. Neon

1. Projeto na região **AWS São Paulo (sa-east-1)** — a mesma das funções (`gru1`).
2. Compute no tamanho **mínimo (0,25 CU)**: o Free tem 100 CU-horas/mês.
3. Copiar a connection string **pooled** (host com `-pooler`):
   `postgresql://usuario:senha@ep-xxx-pooler.sa-east-1.aws.neon.tech/neondb?sslmode=require&channel_binding=require`
   - Pode colar como está: a API troca `postgresql://` por `postgresql+psycopg://` sozinha.
   - **Nunca** versionar essa string nem colá-la em chats/issues.

## 2. Migrations (rodar da sua máquina)

As migrations **não** rodam no deploy (evita que um preview deployment altere o banco de
produção). Rodam manualmente da sua máquina.

A connection string do Neon fica em **`backend/.env.neon`** (gitignored), com uma única linha
`DATABASE_URL=...`. Ela **não** é carregada por padrão: o `backend/.env` continua apontando para o
SQLite local, então `start.bat`, `setup.bat` e os testes nunca tocam a produção. Para um comando
contra o Neon, escolha o arquivo explicitamente (Git Bash):

```bash
cd backend
NEXFI_ENV_FILE=.env.neon .venv/Scripts/alembic upgrade head
```

No PowerShell: `$env:NEXFI_ENV_FILE=".env.neon"; .venv\Scripts\alembic upgrade head; Remove-Item Env:NEXFI_ENV_FILE`

O administrador de produção já existe no Neon. Novos usuários são criados pela tela
**Admin → Usuários** do próprio app.

> O seed de demonstração (`python -m app.seeds.seed`) se recusa a rodar fora de SQLite/localhost:
> ele cria um ADMIN com senha pública e dados fictícios.

## 3. Projeto na Vercel

1. **Add New → Project** → importar `joaoabdala/NexFi`.
2. **Root Directory: `backend`**. Framework: detectado como **FastAPI**.
3. Em *Root Directory*, manter marcada a opção de **incluir arquivos fora do Root Directory no
   build** (padrão) — o build precisa ler `../frontend`.
4. Build Command, região e limites já vêm do `backend/vercel.json` — não precisa preencher nada.
5. **Environment Variables** — marque **só Production**:

| Variável | Valor |
|---|---|
| `DATABASE_URL` | connection string pooled do Neon |
| `SECRET_KEY` | aleatória, 64+ caracteres — `python -c "import secrets; print(secrets.token_urlsafe(64))"` |
| `ENVIRONMENT` | `production` (a API se recusa a subir com a SECRET_KEY padrão) |

`CORS_ORIGINS` e `VITE_API_URL` **não** são necessárias em produção (mesmo domínio).

Travas de produção (ativas com `ENVIRONMENT=production` **ou** automaticamente na Vercel, via
`VERCEL=1`): a API **não sobe** se a `SECRET_KEY` tiver menos de 32 caracteres ou for a de
exemplo, nem se `DATABASE_URL` estiver faltando (cairia no SQLite). Se o deploy der erro 500 em
tudo, confira os logs da função: a mensagem diz qual variável falta. `/docs` e
`/openapi.json` ficam desativados em produção.

6. **Deploy**. Conferir:
   - `https://<projeto>.vercel.app/health` → `{"status":"ok"}`
   - `https://<projeto>.vercel.app/` → tela de login
   - Login com o administrador de produção (já criado no Neon).

> **Previews (branches/PRs):** não coloque `DATABASE_URL`/`SECRET_KEY` de produção em Preview —
> todo branch enviado ao GitHub rodaria código ainda não revisado contra os dados reais, com a
> chave que assina as sessões. Sem essas variáveis, o preview simplesmente não sobe (as travas de
> produção barram). Se quiser previews funcionais, use a integração Neon ↔ Vercel (cria um branch
> isolado do banco por preview) com uma `SECRET_KEY` diferente, e mantenha a *Deployment
> Protection* da Vercel ligada (padrão) para que só você acesse as URLs de preview.

Segurança já configurada no `backend/vercel.json` (vale para todas as respostas): CSP restrita
(scripts só do próprio domínio; estilos inline e Google Fonts liberados), `X-Frame-Options: DENY`,
`X-Content-Type-Options: nosniff`, `Referrer-Policy` e `Permissions-Policy`. Ao adicionar um
serviço externo no frontend (analytics, fontes, imagens de outro domínio), a CSP precisa ser
ajustada — senão o navegador bloqueia e registra o erro no console.

## Migrations pendentes

Sempre que um commit trouxer arquivo novo em `backend/alembic/versions/`, rode antes do deploy:

```bash
cd backend
NEXFI_ENV_FILE=.env.neon .venv/Scripts/alembic upgrade head
```

Última migration: `a5c70d7ccfe2` (tabela `login_throttles`, limite de tentativas de login).

## Simular a produção localmente

```bash
cd backend
bash -c "$(python -c "import json;print(json.load(open('vercel.json'))['buildCommand'])")"
```

Depois suba o preset `nexfi-single-domain` do `.claude/launch.json` (uvicorn na porta 8001,
usando o SQLite local) e abra http://localhost:8001 — é o mesmo arranjo de produção: front e
API no mesmo domínio. `backend/public/` é gerado e fica fora do git.

## Comportamentos esperados no plano Free

- **Primeiro acesso após inatividade é mais lento** (~1–2 s): o Neon suspende o compute após
  5 min parado e a função Python também tem cold start. Os acessos seguintes são normais.
- Storage do Neon Free: 0,5 GB — sobra para anos de uso pessoal (uma transação ocupa ~0,5–1 KB
  com índices; 300 lançamentos/mês ≈ 5–10 MB/ano). O schema vazio ocupa ~8,6 MB. Tokens de
  sessão antigos são apagados automaticamente a cada login/refresh. Acima de 0,5 GB o Neon
  bloqueia escritas.
