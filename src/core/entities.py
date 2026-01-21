from dataclasses import dataclass
from datetime import datetime
from typing import Optional, List


@dataclass
class Account:
    username: str
    user_id: Optional[str] = None
    auth_file_path: Optional[str] = None
    last_synced_at: Optional[datetime] = None
    id: Optional[int] = None


@dataclass
class Tweet:
    rest_id: str
    text: str
    author_handle: str
    author_name: str
    created_at: datetime
    media_blobs: Optional[str] = None  # JSON string of media URLs
    raw_data: Optional[str] = None  # Full JSON response
    quoted_status_id: Optional[str] = None  # ID of the quoted tweet

    # Relationships
    quoted_tweet: Optional["Tweet"] = None
    account_id: Optional[int] = None  # The account that bookmarked this
