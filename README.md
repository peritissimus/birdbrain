# Birdbrain

A local Twitter/X bookmark archiver with AI-powered classification. Uses a browser extension to capture bookmarks and stores them in SQLite with automatic topic categorization and summaries.

## Features

- **Bookmark Capture** - Browser extension intercepts Twitter's GraphQL responses as you scroll
- **AI Classification** - Automatic topic tagging and summaries using Groq (Llama 3.3 70B)
- **Smart Hydration** - Detects truncated tweets and missing quotes, auto-completes when you view them
- **Modern Frontend** - Twitter-like dark UI built with SvelteKit
- **Background Processing** - Celery + Redis for async classification tasks
- **Search & Filter** - Full-text search across tweets, authors, and AI summaries

## Quick Start

### 1. Install Dependencies

```bash
# Install uv (Python package manager)
curl -LsSf https://astral.sh/uv/install.sh | sh

# Initialize everything (Python deps, DB, frontend)
make init
```

### 2. Configure Environment

Create a `.env` file:

```env
GROQ_API_KEY=gsk_your_api_key_here
REDIS_URL=redis://localhost:6379/0
```

Get your Groq API key at: https://console.groq.com/

### 3. Start Services

```bash
# Terminal 1 - Redis (required for background tasks)
redis-server
# OR: docker run -p 6379:6379 redis

# Terminal 2 - Celery worker
make worker

# Terminal 3 - API server (port 8787)
make serve

# Terminal 4 - Frontend (port 5173)
make frontend
```

### 4. Install Browser Extension

**Chrome**
1. Open Chrome and navigate to `chrome://extensions/`
2. Enable **Developer mode** (toggle in top-right corner)
3. Click **Load unpacked**
4. Select the `chrome_extension` folder

**Firefox**
1. Open Firefox and navigate to `about:debugging#/runtime/this-firefox`
2. Click **Load Temporary Add-on...**
3. Select `firefox_extension/manifest.json`

### 5. Sync Your Bookmarks

1. Go to https://x.com/i/bookmarks
2. Scroll through your bookmarks - they're automatically captured
3. View them at http://localhost:5173

## Architecture

```
birdbrain/
├── src/
│   ├── core/              # Domain entities & interfaces
│   │   ├── entities.py    # Tweet, Account dataclasses
│   │   ├── interfaces.py  # Repository & Classifier ABCs
│   │   └── value_objects.py
│   ├── adapters/          # Interface implementations
│   │   ├── db/            # SQLAlchemy models & repository
│   │   ├── ai/            # Groq classifier
│   │   └── twitter/       # GraphQL response parser
│   ├── use_cases/         # Business logic
│   │   ├── sync_bookmarks.py
│   │   └── classify_tweets.py
│   └── infrastructure/    # External concerns
│       ├── api/           # FastAPI server
│       ├── cli/           # CLI commands
│       ├── config.py      # Pydantic settings
│       ├── database.py    # SQLAlchemy engine
│       ├── celery_app.py  # Celery configuration
│       └── tasks.py       # Background tasks
├── chrome_extension/      # Chrome extension (MV3)
├── firefox_extension/     # Firefox extension (MV3)
│   ├── manifest.json
│   ├── background.js      # Syncs incomplete tweets list
│   ├── hook.js            # Intercepts GraphQL (MAIN world)
│   └── content.js         # Sends data to API (ISOLATED world)
└── frontend/              # SvelteKit UI
    └── src/
        ├── routes/        # Pages
        └── lib/           # Components & API client
```

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/bookmarks/ingest` | Receive bookmarks from extension |
| GET | `/api/bookmarks` | List bookmarks (with search/filter) |
| GET | `/api/topics` | Get all topics with counts |
| GET | `/api/topics/{name}/summary` | Generate AI summary for topic |
| GET | `/api/stats` | Classification statistics |
| POST | `/api/tweets/classify` | Trigger classification |
| POST | `/api/bookmarks/{id}/reclassify` | Reclassify single bookmark |
| POST | `/api/bookmarks/reclassify-all` | Reclassify all bookmarks |
| DELETE | `/api/bookmarks/{id}` | Delete a bookmark |
| GET | `/api/tweets/incomplete` | List tweets needing hydration |
| POST | `/api/tweets/{id}/hydrate` | Update with full tweet data |

## Smart Hydration

Some bookmarks may have:
- **Truncated text** - Long tweets cut off in the timeline
- **Missing quotes** - Quoted tweet data not included

Birdbrain tracks these and automatically hydrates them when you view the full tweet:

1. Extension syncs list of incomplete tweet IDs on startup
2. When you visit a tweet page (`x.com/{user}/status/{id}`), extension checks if it needs hydration
3. If yes, captures full data and sends to `/api/tweets/{id}/hydrate`
4. Server updates the tweet and re-queues for classification

## Make Commands

```bash
make init          # Complete setup (deps, db, frontend)
make serve         # Start API server (port 8787)
make worker        # Start Celery worker
make frontend      # Start frontend dev server (port 5173)
make classify      # Run classification on pending tweets
make stats         # Show classification statistics
make clean         # Remove database and cache files
make help          # Show all commands
```

## Configuration

All settings can be configured via environment variables or `.env` file:

| Variable | Default | Description |
|----------|---------|-------------|
| `DATABASE_URL` | `sqlite:///birdbrain.db` | Database connection |
| `SERVER_PORT` | `8787` | API server port |
| `REDIS_URL` | `redis://localhost:6379/0` | Redis connection |
| `GROQ_API_KEY` | - | Groq API key (required for AI) |
| `GROQ_MODEL` | `llama-3.3-70b-versatile` | LLM model to use |
| `CLASSIFICATION_ENABLED` | `true` | Enable auto-classification |
| `CLASSIFICATION_BATCH_SIZE` | `20` | Tweets per classification batch |

## Tech Stack

- **Backend**: Python, FastAPI, SQLAlchemy, Celery
- **AI**: Groq API (Llama 3.3 70B)
- **Frontend**: SvelteKit 5, TypeScript
- **Database**: SQLite
- **Queue**: Redis + Celery
- **Extension**: Chrome + Firefox (Manifest V3)

## License

MIT
