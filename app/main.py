import logging

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from app.api.webhook import router as webhook_router
from fastapi.exceptions import RequestValidationError

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
)

logger = logging.getLogger(__name__)

app = FastAPI(
    title="Agentic Incident Flow",
    version="1.0.0",
)

app.include_router(webhook_router, tags=["webhook"])


@app.get("/")
async def root():
    return {"message": "Agentic Incident Flow API is running!"}


@app.get("/health")
async def health():
    return {"status": "ok"}


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(
    request: Request,
    exc: RequestValidationError,
) -> JSONResponse:
    body = await request.body()

    logger.warning(
        "Validation error on incoming webhook: %s | raw body: %s",
        exc.errors(),
        body.decode("utf-8", errors="replace"),
    )

    return JSONResponse(
        status_code=422,
        content={"detail": exc.errors()},
    )
