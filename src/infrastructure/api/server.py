from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from typing import Dict, Any
from src.infrastructure.database import get_db
from src.adapters.db.repository import SqlAlchemyRepository
from src.use_cases.sync_bookmarks import sync_bookmarks

app = FastAPI()

# Enable CORS for Chrome Extension
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, restrict to extension ID
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.post("/api/bookmarks/ingest")
async def ingest_bookmarks(payload: Dict[str, Any]):
    """
    Receives raw GraphQL response from the Chrome Extension.
    """
    db = next(get_db())
    repo = SqlAlchemyRepository(db)

    processed_count = sync_bookmarks(payload, repo)
    return {"status": "success", "processed_count": processed_count}
