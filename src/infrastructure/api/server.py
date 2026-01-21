from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from typing import Dict, Any
from datetime import datetime
from src.infrastructure.database import get_db
from src.adapters.db.repository import SqlAlchemyRepository
from src.adapters.twitter.parser import TwitterParser
from src.core.entities import Account

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

    # Parse tweets
    tweets = TwitterParser.parse_bookmarks_response(payload)
    count = 0

    # We need a default account to attach these to if we don't have one from the extension
    # For MVP, let's attach to the first account or a "web-import" account
    # Ideally the extension would send the current logged-in user handle too

    # HACK: Just get the first account for now
    accounts = repo.get_all_accounts()
    if not accounts:
        # Create a placeholder if none exists
        account = Account(username="web_imported", last_synced_at=datetime.now())
        account = repo.save_account(account)
    else:
        account = accounts[0]

    for tweet in tweets:
        tweet.account_id = account.id
        repo.save_tweet(tweet)
        count += 1

    return {"status": "success", "processed_count": count}
