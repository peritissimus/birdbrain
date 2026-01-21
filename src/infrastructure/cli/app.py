import asyncio
import typer
from rich.console import Console
from rich.table import Table
from src.infrastructure.database import init_db, get_db
from src.adapters.db.repository import SqlAlchemyRepository
from src.infrastructure.config import get_settings
import uvicorn
from src.infrastructure.api.server import app as api_app

app = typer.Typer()
console = Console()


def get_repo():
    db = next(get_db())
    return SqlAlchemyRepository(db)


@app.command()
def init():
    """Initialize the database."""
    init_db()
    console.print("[green]Database initialized![/green]")


@app.command()
def login(username: str):
    """Deprecated. Use Chrome extension sync."""
    console.print(
        "[yellow]Login via CLI is disabled. Use the Chrome extension flow instead.[/yellow]"
    )
    console.print("Start the API server with: uv run main.py serve")
    console.print("Then sync bookmarks from Chrome.")
    return


@app.command()
def sync(username: str):
    """Deprecated. Use Chrome extension sync."""
    console.print(
        "[yellow]CLI sync is disabled. Use the Chrome extension flow instead.[/yellow]"
    )
    console.print("Start the API server with: uv run main.py serve")
    console.print("Then sync bookmarks from Chrome.")
    return


@app.command()
def import_curl(curl_command: str):
    """Deprecated. Use Chrome extension sync."""
    console.print(
        "[yellow]cURL import is disabled. Use the Chrome extension flow instead.[/yellow]"
    )
    console.print("Start the API server with: uv run main.py serve")
    console.print("Then sync bookmarks from Chrome.")
    return


@app.command()
def list(username: str):
    """List stored bookmarks for an account."""
    repo = get_repo()
    account = repo.get_account_by_username(username)
    if not account:
        console.print("[red]Account not found.[/red]")
        return

    if account.id is None:
        console.print("[red]Account ID is missing.[/red]")
        return

    tweets = repo.get_bookmarks_for_account(account.id)

    table = Table(title=f"Bookmarks for {username}")
    table.add_column("Date", style="cyan")
    table.add_column("Author", style="magenta")
    table.add_column("Text", style="white")
    table.add_column("Topics", style="green")

    for t in tweets:
        topics_str = ", ".join(t.topics) if t.topics else "-"
        table.add_row(
            t.created_at.strftime("%Y-%m-%d"),
            f"@{t.author_handle}",
            t.text[:50] + "..." if t.text and len(t.text) > 50 else t.text,
            topics_str[:30] + "..." if len(topics_str) > 30 else topics_str,
        )

    console.print(table)


@app.command()
def classify(batch_size: int = 20):
    """Run AI classification on pending tweets."""
    settings = get_settings()

    if not settings.groq_api_key:
        console.print("[red]GROQ_API_KEY not configured.[/red]")
        console.print("Set it in your .env file or environment:")
        console.print("  export GROQ_API_KEY=gsk_xxx")
        return

    from src.adapters.ai.groq_classifier import GroqTweetClassifier
    from src.infrastructure.ai.groq_client import GroqConfig
    from src.use_cases.classify_tweets import classify_pending_tweets

    config = GroqConfig(
        api_key=settings.groq_api_key,
        model=settings.groq_model,
        base_url=settings.groq_base_url,
        timeout=settings.groq_timeout,
    )

    repo = get_repo()
    classifier = GroqTweetClassifier(config)

    console.print(f"[cyan]Classifying up to {batch_size} tweets...[/cyan]")

    async def run():
        async with classifier:
            return await classify_pending_tweets(repo, classifier, batch_size)

    result = asyncio.run(run())

    if result.get("skipped"):
        console.print(f"[yellow]Skipped: {result.get('reason')}[/yellow]")
    elif result.get("processed", 0) == 0:
        console.print("[green]No pending tweets to classify.[/green]")
    else:
        console.print(
            f"[green]Classified {result['success']}/{result['processed']} tweets[/green]"
        )
        if result.get("failed", 0) > 0:
            console.print(f"[yellow]Failed: {result['failed']}[/yellow]")


@app.command()
def stats():
    """Show classification statistics."""
    from sqlalchemy import func
    from src.adapters.db.models import TweetModel
    from src.infrastructure.database import SessionLocal

    db = SessionLocal()
    try:
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

        table = Table(title="Classification Statistics")
        table.add_column("Status", style="cyan")
        table.add_column("Count", style="magenta")

        table.add_row("Total Tweets", str(total))
        table.add_row("Pending", str(pending))
        table.add_row("Completed", str(completed))
        table.add_row("Failed", str(failed))

        console.print(table)
    finally:
        db.close()


@app.command()
def serve(port: int = None):
    """Start the API server for Chrome Extension sync."""
    settings = get_settings()
    port = port or settings.server_port
    console.print(f"[bold green]Starting API server on port {port}...[/bold green]")
    console.print("Install the extension in 'chrome_extension/' folder to sync.")

    if settings.groq_api_key:
        console.print(f"[cyan]AI Classification: Enabled (model: {settings.groq_model})[/cyan]")
    else:
        console.print("[yellow]AI Classification: Disabled (set GROQ_API_KEY to enable)[/yellow]")

    uvicorn.run(api_app, host=settings.server_host, port=port)


if __name__ == "__main__":
    app()
