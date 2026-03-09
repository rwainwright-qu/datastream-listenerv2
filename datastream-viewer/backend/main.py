from fastapi import FastAPI, HTTPException, Request, Depends
from fastapi.responses import StreamingResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from pymongo import MongoClient
from pydantic import BaseModel
from typing import Optional
import asyncio
import json
import os
from datetime import datetime
import secrets
import base64

app = FastAPI()

# CORS for development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# MongoDB connection
MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017")
DB_NAME = os.getenv("DB_NAME", "datastream")
COLLECTION_NAME = os.getenv("COLLECTION_NAME", "events")

client = MongoClient(MONGO_URI)
db = client[DB_NAME]
collection = db[COLLECTION_NAME]

# Auth credentials
AUTH_USER = os.getenv("AUTH_USER", "admin")
AUTH_PASS = os.getenv("AUTH_PASS", "admin")

# SSE clients
sse_clients = set()


class Event(BaseModel):
    companyId: Optional[int] = None
    locationId: Optional[int] = None
    entityType: Optional[str] = None
    eventType: Optional[str] = None
    
    class Config:
        extra = "allow"  # Allow any additional fields


async def verify_auth(request: Request):
    auth = request.headers.get("Authorization")
    if not auth or not auth.startswith("Basic "):
        raise HTTPException(401, "Unauthorized")
    
    try:
        decoded = base64.b64decode(auth.split(" ")[1]).decode()
        username, password = decoded.split(":", 1)
        if username != AUTH_USER or password != AUTH_PASS:
            raise HTTPException(401, "Unauthorized")
    except:
        raise HTTPException(401, "Unauthorized")


@app.post("/api/events")
async def create_event(event: Event, _: None = Depends(verify_auth)):
    doc = event.model_dump()
    doc["timestamp"] = datetime.utcnow()
    
    result = collection.insert_one(doc)
    doc["_id"] = str(result.inserted_id)
    
    # Notify SSE clients
    await notify_clients(doc)
    
    return {"id": str(result.inserted_id)}


@app.get("/api/events")
async def get_events(
    page: int = 1,
    companyId: Optional[int] = None,
    locationId: Optional[int] = None,
    entityType: Optional[str] = None
):
    query = {}
    if companyId:
        query["companyId"] = companyId
    if locationId:
        query["locationId"] = locationId
    if entityType:
        query["entityType"] = entityType
    
    skip = (page - 1) * 50
    cursor = collection.find(query).sort("_id", -1).skip(skip).limit(50)
    
    events = []
    for doc in cursor:
        doc["_id"] = str(doc["_id"])
        if "timestamp" in doc:
            doc["timestamp"] = doc["timestamp"].isoformat()
        events.append(doc)
    
    total = collection.count_documents(query)
    
    return {
        "events": events,
        "total": total,
        "page": page,
        "pages": (total + 49) // 50
    }


@app.get("/api/events/stream")
async def event_stream(request: Request):
    async def generate():
        queue = asyncio.Queue()
        sse_clients.add(queue)
        try:
            while True:
                if await request.is_disconnected():
                    break
                try:
                    event = await asyncio.wait_for(queue.get(), timeout=30)
                    yield f"data: {json.dumps(event)}\n\n"
                except asyncio.TimeoutError:
                    yield ": keepalive\n\n"
        finally:
            sse_clients.remove(queue)
    
    return StreamingResponse(generate(), media_type="text/event-stream")


async def notify_clients(event):
    event_copy = event.copy()
    event_copy["timestamp"] = event_copy["timestamp"].isoformat()
    for queue in sse_clients:
        await queue.put(event_copy)


# Serve static files (built frontend)
if os.path.exists("static"):
    app.mount("/", StaticFiles(directory="static", html=True), name="static")


@app.get("/health")
async def health():
    return {"status": "ok"}
