from dataclasses import dataclass, field
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
    media_blobs: Optional[str] = None
    raw_data: Optional[str] = None
    quoted_status_id: Optional[str] = None

    # Relationships
    quoted_tweet: Optional["Tweet"] = None
    account_id: Optional[int] = None

    # AI Classification fields
    topics: Optional[List[str]] = field(default=None)
    summary: Optional[str] = None
    classified_at: Optional[datetime] = None
    classification_status: str = "pending"
    classification_retry_count: int = 0
    classification_model: Optional[str] = None
