from typing import List, Optional
from sqlalchemy.orm import Session
from src.core.entities import Account, Tweet
from src.core.interfaces import BookmarkRepository
from src.core.value_objects import ClassificationResult
from src.adapters.db.models import AccountModel, TweetModel


class SqlAlchemyRepository(BookmarkRepository):
    def __init__(self, db: Session):
        self.db = db

    def _to_account_entity(self, model: AccountModel) -> Account:
        return Account(
            id=model.id,
            username=model.username,
            user_id=model.user_id,
            auth_file_path=model.auth_file_path,
            last_synced_at=model.last_synced_at,
        )

    def _to_tweet_entity(self, model: TweetModel) -> Tweet:
        return Tweet(
            rest_id=model.rest_id,
            text=model.text,
            author_handle=model.author_handle,
            author_name=model.author_name,
            created_at=model.created_at,
            media_blobs=model.media_blobs,
            raw_data=model.raw_data,
            quoted_status_id=model.quoted_status_id,
            account_id=model.account_id,
            topics=model.topics,
            summary=model.summary,
            classified_at=model.classified_at,
            classification_status=model.classification_status or "pending",
            classification_retry_count=model.classification_retry_count or 0,
            classification_model=model.classification_model,
        )

    def save_account(self, account: Account) -> Account:
        model = (
            self.db.query(AccountModel)
            .filter(AccountModel.username == account.username)
            .first()
        )
        if not model:
            model = AccountModel(username=account.username)
            self.db.add(model)

        if account.user_id:
            model.user_id = account.user_id
        if account.auth_file_path:
            model.auth_file_path = account.auth_file_path
        if account.last_synced_at:
            model.last_synced_at = account.last_synced_at

        self.db.commit()
        self.db.refresh(model)
        return self._to_account_entity(model)

    def get_account_by_username(self, username: str) -> Optional[Account]:
        model = (
            self.db.query(AccountModel)
            .filter(AccountModel.username == username)
            .first()
        )
        if model:
            return self._to_account_entity(model)
        return None

    def get_all_accounts(self) -> List[Account]:
        models = self.db.query(AccountModel).all()
        return [self._to_account_entity(m) for m in models]

    def save_tweet(self, tweet: Tweet) -> Tweet:
        model = (
            self.db.query(TweetModel)
            .filter(TweetModel.rest_id == tweet.rest_id)
            .first()
        )
        if not model:
            model = TweetModel(rest_id=tweet.rest_id)
            self.db.add(model)

        model.text = tweet.text
        model.author_handle = tweet.author_handle
        model.author_name = tweet.author_name
        model.created_at = tweet.created_at
        model.media_blobs = tweet.media_blobs
        model.raw_data = tweet.raw_data
        model.quoted_status_id = tweet.quoted_status_id
        model.account_id = tweet.account_id
        model.classification_status = tweet.classification_status

        self.db.commit()
        self.db.refresh(model)
        return self._to_tweet_entity(model)

    def get_tweet_by_rest_id(self, rest_id: str) -> Optional[Tweet]:
        model = self.db.query(TweetModel).filter(TweetModel.rest_id == rest_id).first()
        if model:
            return self._to_tweet_entity(model)
        return None

    def get_bookmarks_for_account(self, account_id: int) -> List[Tweet]:
        models = (
            self.db.query(TweetModel).filter(TweetModel.account_id == account_id).all()
        )
        return [self._to_tweet_entity(m) for m in models]

    def update_tweet_classification(
        self, rest_id: str, result: ClassificationResult
    ) -> Tweet:
        """Update a tweet with classification results."""
        model = self.db.query(TweetModel).filter(TweetModel.rest_id == rest_id).first()
        if not model:
            raise ValueError(f"Tweet not found: {rest_id}")

        model.topics = result.topics
        model.summary = result.summary
        model.classified_at = result.classified_at
        model.classification_status = "completed"
        model.classification_model = result.model_used

        self.db.commit()
        self.db.refresh(model)
        return self._to_tweet_entity(model)

    def get_unclassified_tweets(self, limit: int = 50) -> List[Tweet]:
        """Get tweets that haven't been classified yet."""
        models = (
            self.db.query(TweetModel)
            .filter(TweetModel.classification_status == "pending")
            .limit(limit)
            .all()
        )
        return [self._to_tweet_entity(m) for m in models]

    def mark_classification_failed(
        self, rest_id: str, error_type: str, retry_count: int
    ) -> None:
        """Mark a tweet as having failed classification."""
        model = self.db.query(TweetModel).filter(TweetModel.rest_id == rest_id).first()
        if model:
            model.classification_status = "failed"
            model.classification_retry_count = retry_count
            self.db.commit()
