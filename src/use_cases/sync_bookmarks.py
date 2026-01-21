from datetime import datetime
from typing import Any, Dict

from src.adapters.twitter.parser import TwitterParser
from src.core.entities import Account
from src.core.interfaces import BookmarkRepository


def _ensure_account(repo: BookmarkRepository) -> Account:
    accounts = repo.get_all_accounts()
    if not accounts:
        account = Account(username="web_imported", last_synced_at=datetime.now())
        return repo.save_account(account)

    account = accounts[0]
    account.last_synced_at = datetime.now()
    return repo.save_account(account)


def sync_bookmarks(
    payload: Dict[str, Any],
    repo: BookmarkRepository,
    parser: type[TwitterParser] = TwitterParser,
) -> int:
    tweets = parser.parse_bookmarks_response(payload)
    account = _ensure_account(repo)

    for tweet in tweets:
        tweet.account_id = account.id
        repo.save_tweet(tweet)

    return len(tweets)
