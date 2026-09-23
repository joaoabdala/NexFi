from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.api.v1.router import api_router
from app.core.config import settings
from app.core.exceptions import NexFiError
from app.core.logging import configure_logging, logger

configure_logging()

app = FastAPI(
    title="NexFi API",
    description="API do NexFi — Personal Finance by Abdala Nexus",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_origin_regex=settings.CORS_ORIGIN_REGEX or None,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    # Frontend e API ficam em domínios diferentes na Vercel e toda requisição leva o header
    # Authorization, o que exige preflight (OPTIONS). Cachear evita um round-trip extra por chamada.
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
