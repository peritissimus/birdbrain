from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware
from typing import Dict, Any, List, Optional

from src.infrastructure.database import get_db, SessionLocal
from src.infrastructure.config import get_settings
from src.adapters.db.repository import SqlAlchemyRepository
from src.adapters.db.models import TweetModel
from src.use_cases.sync_bookmarks import sync_bookmarks

app = FastAPI(title="Birdbrain API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.post("/api/bookmarks/ingest")
async def ingest_bookmarks(payload: Dict[str, Any]):
    """Receives raw GraphQL response from the Chrome Extension."""
    db = next(get_db())
    repo = SqlAlchemyRepository(db)

    processed_count = sync_bookmarks(payload, repo)

    # Queue classification task via Celery
    settings = get_settings()
    if settings.classification_enabled and settings.groq_api_key:
        from src.infrastructure.tasks import classify_tweets_task

        classify_tweets_task.delay(settings.classification_batch_size)

    return {"status": "success", "processed_count": processed_count}


@app.get("/api/bookmarks")
async def get_bookmarks(
    limit: int = Query(50, ge=1, le=500),
    offset: int = Query(0, ge=0),
    topic: Optional[str] = None,
    status: Optional[str] = None,
    q: Optional[str] = Query(None, description="Search query for text, author, or summary"),
):
    """Fetch bookmarks with optional filtering and search."""
    db = SessionLocal()
    try:
        from sqlalchemy import or_

        query = db.query(TweetModel).order_by(TweetModel.created_at.desc())

        if q:
            search_term = f"%{q}%"
            query = query.filter(
                or_(
                    TweetModel.text.ilike(search_term),
                    TweetModel.author_handle.ilike(search_term),
                    TweetModel.author_name.ilike(search_term),
                    TweetModel.summary.ilike(search_term),
                )
            )

        if topic:
            # SQLite JSON compatibility - use LIKE for JSON array search
            query = query.filter(TweetModel.topics.like(f'%"{topic}"%'))

        if status:
            query = query.filter(TweetModel.classification_status == status)

        total = query.count()
        tweets = query.offset(offset).limit(limit).all()

        return {
            "bookmarks": [
                {
                    "id": t.id,
                    "rest_id": t.rest_id,
                    "text": t.text,
                    "author_handle": t.author_handle,
                    "author_name": t.author_name,
                    "created_at": t.created_at.isoformat() if t.created_at else None,
                    "topics": t.topics or [],
                    "summary": t.summary,
                    "classification_status": t.classification_status,
                    "media_urls": t.media_blobs,
                    "quoted_status_id": t.quoted_status_id,
                }
                for t in tweets
            ],
            "total": total,
            "limit": limit,
            "offset": offset,
        }
    finally:
        db.close()


@app.get("/api/topics")
async def get_topics():
    """Get all unique topics with counts."""
    db = SessionLocal()
    try:
        tweets = db.query(TweetModel).filter(TweetModel.topics.isnot(None)).all()
        topic_counts: Dict[str, int] = {}
        for tweet in tweets:
            if tweet.topics:
                for topic in tweet.topics:
                    topic_counts[topic] = topic_counts.get(topic, 0) + 1

        sorted_topics = sorted(topic_counts.items(), key=lambda x: x[1], reverse=True)
        return {"topics": [{"name": t, "count": c} for t, c in sorted_topics]}
    finally:
        db.close()


@app.post("/api/topics/generate-summaries")
async def generate_all_topic_summaries():
    """Generate summaries for all topics."""
    settings = get_settings()
    if not settings.groq_api_key:
        return {"status": "error", "message": "Classifier not configured"}

    db = SessionLocal()
    try:
        # Get all topics
        tweets = db.query(TweetModel).filter(TweetModel.topics.isnot(None)).all()
        topic_names: set = set()
        for tweet in tweets:
            if tweet.topics:
                for topic in tweet.topics:
                    topic_names.add(topic)

        return {"status": "started", "topics": list(topic_names), "count": len(topic_names)}
    finally:
        db.close()


@app.get("/api/topics/{topic_name}/summary")
async def get_topic_summary(topic_name: str):
    """Generate a summary for a topic based on its bookmarks."""
    settings = get_settings()
    if not settings.groq_api_key:
        return {"topic": topic_name, "summary": None, "error": "Classifier not configured"}

    db = SessionLocal()
    try:
        tweets = (
            db.query(TweetModel)
            .filter(TweetModel.topics.like(f'%"{topic_name}"%'))
            .limit(10)
            .all()
        )

        if not tweets:
            return {"topic": topic_name, "summary": None}

        # Build context from tweets
        tweets_text = "\n\n".join(
            [f"- @{t.author_handle}: {t.text[:200]}" for t in tweets]
        )

        import httpx

        prompt = f"""Based on these tweets about "{topic_name}", write a 1-2 sentence summary describing what this topic collection is about. Be concise and informative.

Tweets:
{tweets_text}

Summary:"""

        async with httpx.AsyncClient() as client:
            response = await client.post(
                "https://api.groq.com/openai/v1/chat/completions",
                headers={
                    "Authorization": f"Bearer {settings.groq_api_key}",
                    "Content-Type": "application/json",
                },
                json={
                    "model": settings.groq_model,
                    "messages": [{"role": "user", "content": prompt}],
                    "max_tokens": 150,
                    "temperature": 0.3,
                },
                timeout=30.0,
            )
            response.raise_for_status()
            data = response.json()
            summary = data["choices"][0]["message"]["content"].strip()

        return {"topic": topic_name, "summary": summary}
    except Exception as e:
        return {"topic": topic_name, "summary": None, "error": str(e)}
    finally:
        db.close()


@app.get("/api/stats")
async def get_stats():
    """Get classification statistics."""
    db = SessionLocal()
    try:
        from sqlalchemy import func

        total = db.query(func.count(TweetModel.id)).scalar()
        pending = (
            db.query(func.count(TweetModel.id))
            .filter(TweetModel.classification_status == "pending")
            .scalar()
        )
        completed = (
            db.query(func.count(TweetModel.id))
            .filter(TweetModel.classification_status == "completed")
            .scalar()
        )
        failed = (
            db.query(func.count(TweetModel.id))
            .filter(TweetModel.classification_status == "failed")
            .scalar()
        )

        return {
            "total": total,
            "pending": pending,
            "completed": completed,
            "failed": failed,
        }
    finally:
        db.close()


@app.post("/api/tweets/classify")
async def trigger_classification(batch_size: int = 20):
    """Manually trigger classification of pending tweets via Celery."""
    settings = get_settings()

    if not settings.groq_api_key:
        return {"status": "error", "message": "Classifier not configured. Set GROQ_API_KEY."}

    from src.infrastructure.tasks import classify_tweets_task

    task = classify_tweets_task.delay(batch_size)
    return {"status": "queued", "task_id": task.id}


@app.post("/api/bookmarks/{rest_id}/reclassify")
async def reclassify_bookmark(rest_id: str):
    """Reset a bookmark to pending and queue for reclassification."""
    db = SessionLocal()
    try:
        tweet = db.query(TweetModel).filter(TweetModel.rest_id == rest_id).first()
        if not tweet:
            return {"status": "error", "message": "Bookmark not found"}

        tweet.classification_status = "pending"
        tweet.topics = None
        tweet.summary = None
        tweet.classified_at = None
        db.commit()

        settings = get_settings()
        if settings.groq_api_key:
            from src.infrastructure.tasks import classify_tweets_task
            classify_tweets_task.delay(1)

        return {"status": "queued", "rest_id": rest_id}
    finally:
        db.close()


@app.post("/api/bookmarks/reclassify-all")
async def reclassify_all_bookmarks(status: Optional[str] = None):
    """Reset all bookmarks (or by status) to pending and queue for reclassification."""
    db = SessionLocal()
    try:
        query = db.query(TweetModel)
        if status:
            query = query.filter(TweetModel.classification_status == status)

        count = query.update({
            "classification_status": "pending",
            "topics": None,
            "summary": None,
            "classified_at": None,
        })
        db.commit()

        settings = get_settings()
        if settings.groq_api_key and count > 0:
            from src.infrastructure.tasks import classify_tweets_task
            classify_tweets_task.delay(settings.classification_batch_size)

        return {"status": "queued", "count": count}
    finally:
        db.close()


@app.delete("/api/bookmarks/{rest_id}")
async def delete_bookmark(rest_id: str):
    """Delete a bookmark."""
    db = SessionLocal()
    try:
        tweet = db.query(TweetModel).filter(TweetModel.rest_id == rest_id).first()
        if not tweet:
            return {"status": "error", "message": "Bookmark not found"}

        db.delete(tweet)
        db.commit()
        return {"status": "deleted", "rest_id": rest_id}
    finally:
        db.close()


@app.get("/api/topics/{topic_name}/bookmarks")
async def get_bookmarks_by_topic(
    topic_name: str,
    limit: int = Query(50, ge=1, le=500),
    offset: int = Query(0, ge=0),
):
    """Get all bookmarks for a specific topic."""
    db = SessionLocal()
    try:
        query = (
            db.query(TweetModel)
            .filter(TweetModel.topics.like(f'%"{topic_name}"%'))
            .order_by(TweetModel.created_at.desc())
        )

        total = query.count()
        tweets = query.offset(offset).limit(limit).all()

        return {
            "topic": topic_name,
            "bookmarks": [
                {
                    "id": t.id,
                    "rest_id": t.rest_id,
                    "text": t.text,
                    "author_handle": t.author_handle,
                    "author_name": t.author_name,
                    "created_at": t.created_at.isoformat() if t.created_at else None,
                    "topics": t.topics or [],
                    "summary": t.summary,
                    "classification_status": t.classification_status,
                }
                for t in tweets
            ],
            "total": total,
        }
    finally:
        db.close()


@app.get("/api/tweets/incomplete")
async def get_incomplete_tweets():
    """Get list of tweet IDs that need hydration (truncated or missing quotes)."""
    db = SessionLocal()
    try:
        tweets = (
            db.query(TweetModel)
            .filter(TweetModel.needs_hydration == True)
            .all()
        )
        return {
            "tweets": [
                {
                    "rest_id": t.rest_id,
                    "author_handle": t.author_handle,
                    "is_truncated": t.is_truncated,
                    "is_quote_missing": t.is_quote_missing,
                    "quoted_status_id": t.quoted_status_id,
                }
                for t in tweets
            ],
            "count": len(tweets),
        }
    finally:
        db.close()


@app.post("/api/tweets/{rest_id}/hydrate")
async def hydrate_tweet(rest_id: str, payload: Dict[str, Any]):
    """Update a tweet with full data from viewing the tweet page."""
    from src.adapters.twitter.parser import TwitterParser

    db = SessionLocal()
    try:
        tweet_model = db.query(TweetModel).filter(TweetModel.rest_id == rest_id).first()
        if not tweet_model:
            return {"status": "error", "message": "Tweet not found"}

        # Parse the TweetDetail response
        parsed = TwitterParser.parse_tweet_detail(payload)
        if not parsed:
            return {"status": "error", "message": "Failed to parse tweet data"}

        # Update fields if we got better data
        if parsed.text and len(parsed.text) > len(tweet_model.text or ""):
            tweet_model.text = parsed.text
            tweet_model.is_truncated = False
            # Reset classification since text changed
            tweet_model.classification_status = "pending"
            tweet_model.topics = None
            tweet_model.summary = None

        # Update raw_data with new data
        tweet_model.raw_data = parsed.raw_data

        # Check if we got the quoted tweet
        if tweet_model.is_quote_missing and parsed.quoted_status_id:
            quoted_tweet = TwitterParser.extract_quoted_tweet(payload)
            if quoted_tweet:
                existing_quoted = db.query(TweetModel).filter(
                    TweetModel.rest_id == quoted_tweet.rest_id
                ).first()
                if not existing_quoted:
                    quoted_model = TweetModel(
                        rest_id=quoted_tweet.rest_id,
                        text=quoted_tweet.text,
                        author_handle=quoted_tweet.author_handle,
                        author_name=quoted_tweet.author_name,
                        created_at=quoted_tweet.created_at,
                        media_blobs=quoted_tweet.media_blobs,
                        raw_data=quoted_tweet.raw_data,
                        classification_status="pending",
                    )
                    db.add(quoted_model)
                tweet_model.is_quote_missing = False

        # Update needs_hydration flag
        tweet_model.needs_hydration = tweet_model.is_truncated or tweet_model.is_quote_missing

        db.commit()

        # Trigger classification if needed
        settings = get_settings()
        if settings.groq_api_key and tweet_model.classification_status == "pending":
            from src.infrastructure.tasks import classify_tweets_task
            classify_tweets_task.delay(1)

        return {
            "status": "success",
            "rest_id": rest_id,
            "is_truncated": tweet_model.is_truncated,
            "is_quote_missing": tweet_model.is_quote_missing,
            "needs_hydration": tweet_model.needs_hydration,
        }
    finally:
        db.close()


@app.get("/api/health")
async def health_check():
    """Health check endpoint."""
    settings = get_settings()
    return {
        "status": "ok",
        "classification_enabled": settings.classification_enabled,
        "classifier_configured": bool(settings.groq_api_key),
        "redis_url": settings.redis_url,
    }
