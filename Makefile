.PHONY: init install db-init serve worker clean help extension-info classify stats frontend frontend-build

# Default target
help:
	@echo "Birdbrain - Twitter Bookmark Archiver"
	@echo ""
	@echo "Usage:"
	@echo "  make init          - Complete setup (install deps, init db, show extension info)"
	@echo "  make install       - Install Python dependencies"
	@echo "  make db-init       - Initialize the database"
	@echo "  make serve         - Start the API server"
	@echo "  make worker        - Start the Celery worker for background tasks"
	@echo "  make frontend      - Start the frontend dev server"
	@echo "  make frontend-build - Build the frontend for production"
	@echo "  make classify      - Run AI classification on pending tweets"
	@echo "  make stats         - Show classification statistics"
	@echo "  make clean         - Remove database and cache files"
	@echo "  make help          - Show this help message"

# Complete initialization
init: install db-init frontend-install extension-info

# Install Python dependencies
install:
	@echo "Installing Python dependencies..."
	uv sync
	@echo "Python dependencies installed."

# Install frontend dependencies
frontend-install:
	@echo "Installing frontend dependencies..."
	cd frontend && npm install
	@echo "Frontend dependencies installed."

# Initialize database
db-init:
	@echo "Initializing database..."
	uv run python -c "from src.infrastructure.database import init_db; init_db()"
	@echo "Database initialized."

# Start the API server
serve:
	@echo "Starting Birdbrain API server..."
	uv run python -c "from src.infrastructure.cli.app import app; app()" serve

# Start the Celery worker
worker:
	@echo "Starting Celery worker..."
	uv run celery -A src.infrastructure.celery_app worker --loglevel=info

# Start frontend dev server
frontend:
	@echo "Starting frontend dev server..."
	cd frontend && npm run dev

# Build frontend for production
frontend-build:
	@echo "Building frontend..."
	cd frontend && npm run build

# Run AI classification on pending tweets (via CLI)
classify:
	@echo "Running AI classification..."
	uv run python -c "from src.infrastructure.cli.app import app; app()" classify

# Show classification statistics
stats:
	uv run python -c "from src.infrastructure.cli.app import app; app()" stats

# Show extension installation instructions
extension-info:
	@echo ""
	@echo "=============================================="
	@echo "  Browser Extension Installation Instructions"
	@echo "=============================================="
	@echo ""
	@echo "Chrome:"
	@echo "1. Open Chrome and navigate to:"
	@echo "   chrome://extensions/"
	@echo ""
	@echo "2. Enable 'Developer mode' (toggle in top-right corner)"
	@echo ""
	@echo "3. Click 'Load unpacked' button"
	@echo ""
	@echo "4. Select the folder:"
	@echo "   $(CURDIR)/chrome_extension"
	@echo ""
	@echo "5. The 'Birdbrain Sync' extension should now appear"
	@echo ""
	@echo "Firefox:"
	@echo "1. Open Firefox and navigate to:"
	@echo "   about:debugging#/runtime/this-firefox"
	@echo ""
	@echo "2. Click 'Load Temporary Add-on...'"
	@echo ""
	@echo "3. Select the manifest file:"
	@echo "   $(CURDIR)/firefox_extension/manifest.json"
	@echo ""
	@echo "=============================================="
	@echo "  Configuration"
	@echo "=============================================="
	@echo ""
	@echo "Create a .env file with:"
	@echo ""
	@echo "  GROQ_API_KEY=gsk_xxx"
	@echo "  REDIS_URL=redis://localhost:6379/0"
	@echo ""
	@echo "Get your Groq API key at: https://console.groq.com/"
	@echo ""
	@echo "=============================================="
	@echo "  Usage"
	@echo "=============================================="
	@echo ""
	@echo "1. Start Redis (required for background tasks):"
	@echo "   redis-server"
	@echo "   OR: docker run -p 6379:6379 redis"
	@echo ""
	@echo "2. Start the Celery worker:"
	@echo "   make worker"
	@echo ""
	@echo "3. Start the API server (in another terminal):"
	@echo "   make serve"
	@echo ""
	@echo "4. Start the frontend (in another terminal):"
	@echo "   make frontend"
	@echo ""
	@echo "5. Go to https://x.com/i/bookmarks in Chrome"
	@echo ""
	@echo "6. Scroll through your bookmarks - they will be"
	@echo "   automatically captured, saved, and classified"
	@echo ""
	@echo "7. View your bookmarks at http://localhost:5173"
	@echo ""
	@echo "=============================================="

# Clean up
clean:
	@echo "Cleaning up..."
	rm -f birdbrain.db
	rm -rf __pycache__ .pytest_cache
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	@echo "Cleanup complete."
