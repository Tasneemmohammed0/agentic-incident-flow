from fastapi import FastAPI

app = FastAPI(
    title="Agentic Incident Flow",
    version="1.0.0",
)


@app.get("/")
async def root():
    return {"message": "Agentic Incident Flow API is running!"}
