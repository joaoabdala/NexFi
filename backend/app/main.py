import mimetypes
from pathlib import Path

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse

from app.api.v1.router import api_router
from app.core.config import settings
from app.core.exceptions import NexFiError
from app.core.logging import configure_logging, logger

configure_logging()

app = FastAPI(
    title="NexFi API",
    description="API do NexFi — Personal Finance by Abdala Nexus",
    version="1.0.0",
    # Em produção não expõe o mapa completo da API (/docs, /redoc, /openapi.json).
    docs_url=None if settings.is_production else "/docs",
    redoc_url=None if settings.is_production else "/redoc",
    openapi_url=None if settings.is_production else "/openapi.json",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_origin_regex=settings.CORS_ORIGIN_REGEX or None,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    # Em produção front e API compartilham o domínio (sem CORS); isto vale para o dev local
    # (Vite na 5173 → API na 8000). Cachear o preflight evita um OPTIONS extra por chamada.
    max_age=86400,
)


@app.exception_handler(NexFiError)
async def nexfi_error_handler(request: Request, exc: NexFiError) -> JSONResponse:
    return JSONResponse(status_code=exc.status_code, content={"detail": exc.message})


@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    logger.exception("Unhandled error on %s %s", request.method, request.url.path)
    return JSONResponse(status_code=500, content={"detail": "Erro interno do servidor."})


app.include_router(api_router, prefix="/api/v1")


@app.get("/health", tags=["health"])
def health() -> dict[str, str]:
    return {"status": "ok"}


# --- Frontend (SPA) -------------------------------------------------------------------------
# Em produção o build do frontend é copiado para backend/public/ (ver vercel.json) e entra no
# pacote da função. Esta rota serve os arquivos de public/ (JS/CSS/ícones) e, para rotas do React
# Router acessadas diretamente (ex.: F5 em /transacoes), devolve o index.html.
# (A Vercel NÃO promove ao CDN um public/ gerado durante o build — confirmado no 1º deploy, quando
# os /assets davam 404 e a tela ficava preta. Na frente há a Cloudflare, que cacheia os assets.)
# Localmente, sem build em public/, só responde 404 (o frontend roda no Vite).
# Precisa ser a última rota registrada, para não sombrear a API.
PUBLIC_DIR = Path(__file__).resolve().parent.parent / "public"
# O Linux da Vercel não conhece a extensão do manifest do PWA (sairia application/octet-stream).
mimetypes.add_type("application/manifest+json", ".webmanifest")

# Arquivos em /assets têm hash do conteúdo no nome: podem ficar em cache "para sempre".
# s-maxage/CDN-Cache-Control deixam a Vercel e a Cloudflare guardarem também.
IMMUTABLE = "public, max-age=31536000, s-maxage=31536000, immutable"
# Respostas de erro nunca podem ir para cache — um 404 cacheado de um asset deixa o app fora do ar
# até alguém limpar o cache da Cloudflare.
NO_STORE = {"Cache-Control": "no-store"}


def _not_found(detail: str) -> HTTPException:
    return HTTPException(status_code=404, detail=detail, headers=NO_STORE)


# GET e HEAD: previews de link e monitores de uptime costumam checar a página com HEAD.
@app.api_route("/{full_path:path}", methods=["GET", "HEAD"], include_in_schema=False)
def spa_fallback(full_path: str) -> FileResponse:
    if full_path == "api" or full_path.startswith("api/"):
        raise _not_found("Recurso não encontrado.")

    candidate = (PUBLIC_DIR / full_path).resolve()
    if full_path and candidate.is_file() and PUBLIC_DIR in candidate.parents:
        # Arquivos de nome fixo (favicon, og-image, manifest) mudam sem trocar de nome: cache curto.
        cache = IMMUTABLE if full_path.startswith("assets/") else "public, max-age=300"
        return FileResponse(candidate, headers={"Cache-Control": cache, "CDN-Cache-Control": cache})

    # Arquivo inexistente (ex.: chunk antigo após um deploy) deve dar 404, não o index.html —
    # senão o navegador tentaria executar HTML como JavaScript.
    if "." in full_path.rsplit("/", 1)[-1]:
        raise _not_found("Arquivo não encontrado.")

    index = PUBLIC_DIR / "index.html"
    if not index.is_file():
        raise _not_found("Frontend não publicado neste ambiente.")
    return FileResponse(index, headers={"Cache-Control": "no-cache"})
