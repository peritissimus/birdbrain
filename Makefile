.PHONY: init install db-init serve clean help extension-info

# Default target
help:
	@echo "Birdbrain - Twitter Bookmark Archiver"
	@echo ""
	@echo "Usage:"
	@echo "  make init      - Complete setup (install deps, init db, show extension info)"
	@echo "  make install   - Install Python dependencies"
	@echo "  make db-init   - Initialize the database"
	@echo "  make serve     - Start the API server"
	@echo "  make clean     - Remove database and cache files"
	@echo "  make help      - Show this help message"

# Complete initialization
init: install db-init extension-info

# Install dependencies
install:
	@echo "Installing dependencies..."
	uv sync
	@echo "Dependencies installed."

# Initialize database
db-init:
	@echo "Initializing database..."
	uv run python -c "from src.infrastructure.database import init_db; init_db()"
	@echo "Database initialized."

# Start the API server
serve:
	@echo "Starting Birdbrain API server..."
	uv run python -c "from src.infrastructure.cli.app import app; app()" serve

# Show extension installation instructions
extension-info:
	@echo ""
	@echo "=============================================="
	@echo "  Chrome Extension Installation Instructions"
	@echo "=============================================="
	@echo ""
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
	@echo "=============================================="
	@echo "  Usage"
	@echo "=============================================="
	@echo ""
	@echo "1. Start the API server:"
	@echo "   make serve"
	@echo ""
	@echo "2. Go to https://x.com/i/bookmarks in Chrome"
	@echo ""
	@echo "3. Scroll through your bookmarks - they will be"
	@echo "   automatically captured and sent to Birdbrain"
	@echo ""
	@echo "4. Click the extension icon to see sync status"
	@echo ""
	@echo "=============================================="

# Clean up
clean:
	@echo "Cleaning up..."
	rm -f birdbrain.db
	rm -rf __pycache__ .pytest_cache
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	@echo "Cleanup complete."
