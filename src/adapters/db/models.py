from sqlalchemy import Column, Integer, String, DateTime, Text, ForeignKey, JSON, Boolean
from sqlalchemy.orm import relationship
from src.infrastructure.database import Base


class AccountModel(Base):
    __tablename__ = "accounts"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True, nullable=False)
    user_id = Column(String, nullable=True)
    auth_file_path = Column(String, nullable=True)
    last_synced_at = Column(DateTime, nullable=True)

    bookmarks = relationship("TweetModel", back_populates="account")


class TweetModel(Base):
    __tablename__ = "tweets"

    id = Column(Integer, primary_key=True, index=True)
    rest_id = Column(String, unique=True, index=True, nullable=False)
    text = Column(Text, nullable=True)
    author_handle = Column(String, nullable=True)
    author_name = Column(String, nullable=True)
    created_at = Column(DateTime, nullable=True)
    media_blobs = Column(Text, nullable=True)
    raw_data = Column(Text, nullable=True)

    quoted_status_id = Column(String, ForeignKey("tweets.rest_id"), nullable=True)
    account_id = Column(Integer, ForeignKey("accounts.id"), nullable=True)

    # AI Classification fields
    topics = Column(JSON, nullable=True)
    summary = Column(Text, nullable=True)
    classified_at = Column(DateTime, nullable=True)
    classification_status = Column(String, default="pending", index=True, nullable=False)
    classification_retry_count = Column(Integer, default=0)
    classification_model = Column(String, nullable=True)

    # Sync/Hydration tracking
    is_truncated = Column(Boolean, default=False, nullable=False)
    is_quote_missing = Column(Boolean, default=False, nullable=False)
    needs_hydration = Column(Boolean, default=False, index=True, nullable=False)

    account = relationship("AccountModel", back_populates="bookmarks")
    quoted_tweet = relationship("TweetModel", remote_side=[rest_id])
