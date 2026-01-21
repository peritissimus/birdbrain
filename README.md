# Birdbrain

A local bookmark archive that uses a Chrome Extension to capture your Twitter/X bookmarks and store them in SQLite.

## Installation

1. Install `uv`:
   ```bash
   curl -LsSf https://astral.sh/uv/install.sh | sh
   ```
2. Sync dependencies:
   ```bash
   uv sync
   ```

## Usage (Chrome Extension Default)

### 1. Initialize Database
```bash
uv run main.py init
```

### 2. Start the API Server
```bash
uv run main.py serve
```

### 3. Install the Chrome Extension
1. Open Chrome/Brave/Edge and go to `chrome://extensions`.
2. Enable **Developer mode** (top right).
3. Click **Load unpacked** and select the `chrome_extension` folder in this project.

### 4. Sync Bookmarks
1. Go to your Twitter Bookmarks page (`https://x.com/i/bookmarks`).
2. Click the extension icon and hit **Start Syncing**.
3. Scroll down your bookmarks list. The extension will intercept the data and send it to your local database.

### 5. List Bookmarks
View what you've saved.
```bash
uv run main.py list <your_username>
```

## Notes
- The CLI login/sync methods are disabled. The extension is the default and supported method.

## Architecture
This project follows **Clean Architecture** principles:
- **Core**: Domain Entities and Interfaces (No dependencies).
- **Use Cases**: Business logic (Account Manager, Sync Manager).
- **Adapters**: Implementations (SQLAlchemy Repository, Playwright Scraper).
- **Infrastructure**: CLI, API Server, Config, Database Engine.
