import typer
from rich.console import Console
from rich.table import Table
from src.infrastructure.database import init_db, get_db
from src.adapters.db.repository import SqlAlchemyRepository
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

    for t in tweets:
        table.add_row(
            t.created_at.strftime("%Y-%m-%d"),
            f"@{t.author_handle}",
            t.text[:50] + "..." if t.text and len(t.text) > 50 else t.text,
        )

    console.print(table)


@app.command()
def serve(port: int = 8000):
    """Start the API server for Chrome Extension sync."""
    console.print(f"[bold green]Starting API server on port {port}...[/bold green]")
    console.print("Install the extension in 'chrome_extension/' folder to sync.")
    uvicorn.run(api_app, host="127.0.0.1", port=port)


if __name__ == "__main__":
    app()
