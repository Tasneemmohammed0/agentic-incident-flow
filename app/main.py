from fastapi import FastAPI
from app.api.webhook import router as webhook_router

app = FastAPI(
    title="Agentic Incident Flow",
    version="1.0.0",
)

app.include_router(webhook_router, prefix="/api")


@app.get("/")
async def root():
    return {"message": "Agentic Incident Flow API is running!"}


@app.get("/health")
async def health():
    return {"status": "ok"}
