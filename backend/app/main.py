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
# Em produção o build do frontend é copiado para backend/public/ (ver vercel.json). Na Vercel,
# arquivos existentes em public/ saem direto do CDN e nem chegam aqui; esta rota cobre o resto:
# rotas do React Router acessadas diretamente (ex.: F5 em /transacoes) recebem o index.html.
# Localmente, sem build em public/, só responde 404 (o frontend roda no Vite).
# Precisa ser a última rota registrada, para não sombrear a API.
PUBLIC_DIR = Path(__file__).resolve().parent.parent / "public"


@app.get("/{full_path:path}", include_in_schema=False)
def spa_fallback(full_path: str) -> FileResponse:
    if full_path == "api" or full_path.startswith("api/"):
        raise HTTPException(status_code=404, detail="Recurso não encontrado.")

    candidate = (PUBLIC_DIR / full_path).resolve()
    if full_path and candidate.is_file() and PUBLIC_DIR in candidate.parents:
        return FileResponse(candidate)  # só acontece localmente; na Vercel o CDN serve antes

    # Arquivo inexistente (ex.: chunk antigo após um deploy) deve dar 404, não o index.html —
    # senão o navegador tentaria executar HTML como JavaScript.
    if "." in full_path.rsplit("/", 1)[-1]:
        raise HTTPException(status_code=404, detail="Arquivo não encontrado.")

    index = PUBLIC_DIR / "index.html"
    if not index.is_file():
        raise HTTPException(status_code=404, detail="Frontend não publicado neste ambiente.")
    return FileResponse(index, headers={"Cache-Control": "no-cache"})
