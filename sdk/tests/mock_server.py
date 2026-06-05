"""
Tiny FastAPI server for offline SDK testing.
Run with: py -3.11 -m uvicorn tests.mock_server:app --port 9999
"""
from fastapi import FastAPI, Request

app = FastAPI()

received_batches: list[dict] = []


@app.post("/api/v1/ingest")
async def ingest(request: Request) -> dict:
    body = await request.json()
    received_batches.append(body)
    return {"ingested": len(body.get("events", [])), "skipped": 0}


@app.get("/batches")
async def get_batches() -> list[dict]:
    return received_batches


@app.delete("/batches")
async def clear_batches() -> dict:
    received_batches.clear()
    return {"cleared": True}