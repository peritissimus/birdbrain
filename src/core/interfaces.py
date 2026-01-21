from abc import ABC, abstractmethod
from typing import List, Optional
from .entities import Account, Tweet
from .value_objects import ClassificationResult


class BookmarkRepository(ABC):
    @abstractmethod
    def save_account(self, account: Account) -> Account:
        pass

    @abstractmethod
    def get_account_by_username(self, username: str) -> Optional[Account]:
        pass

    @abstractmethod
    def get_all_accounts(self) -> List[Account]:
        pass

    @abstractmethod
    def save_tweet(self, tweet: Tweet) -> Tweet:
        pass

    @abstractmethod
    def get_tweet_by_rest_id(self, rest_id: str) -> Optional[Tweet]:
        pass

    @abstractmethod
    def get_bookmarks_for_account(self, account_id: int) -> List[Tweet]:
        pass

    @abstractmethod
    def update_tweet_classification(
        self, rest_id: str, result: ClassificationResult
    ) -> Tweet:
        """Update a tweet with classification results."""
        pass

    @abstractmethod
    def get_unclassified_tweets(self, limit: int = 50) -> List[Tweet]:
        """Get tweets that haven't been classified yet."""
        pass

    @abstractmethod
    def mark_classification_failed(
        self, rest_id: str, error_type: str, retry_count: int
    ) -> None:
        """Mark a tweet as having failed classification."""
        pass


class TweetClassifier(ABC):
    """Abstract interface for tweet classification services."""

    @abstractmethod
    async def classify(self, tweet: Tweet) -> ClassificationResult:
        """Classify a single tweet, extracting topics and summary."""
        pass

    @abstractmethod
    async def classify_batch(
        self, tweets: List[Tweet], max_concurrent: int = 5
    ) -> List[tuple[Tweet, Optional[ClassificationResult], Optional[Exception]]]:
        """Classify multiple tweets with concurrency control."""
        pass

    @abstractmethod
    def is_available(self) -> bool:
        """Check if the classifier service is configured and reachable."""
        pass
