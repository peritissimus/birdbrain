from sqlalchemy import Column, Integer, String, DateTime, Text, ForeignKey
from sqlalchemy.orm import relationship
from src.infrastructure.database import Base
from datetime import datetime


class AccountModel(Base):
    __tablename__ = "accounts"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True, nullable=False)
    user_id = Column(String, nullable=True)
    auth_file_path = Column(String, nullable=True)
    last_synced_at = Column(DateTime, nullable=True)

    # Relationship to bookmarks (tweets this account saved)
    bookmarks = relationship("TweetModel", back_populates="account")


class TweetModel(Base):
    __tablename__ = "tweets"

    id = Column(Integer, primary_key=True, index=True)
    rest_id = Column(String, unique=True, index=True, nullable=False)
    text = Column(Text, nullable=True)
    author_handle = Column(String, nullable=True)
    author_name = Column(String, nullable=True)
    created_at = Column(DateTime, nullable=True)
    media_blobs = Column(Text, nullable=True)  # JSON string
    raw_data = Column(Text, nullable=True)  # JSON string

    quoted_status_id = Column(String, ForeignKey("tweets.rest_id"), nullable=True)
    account_id = Column(Integer, ForeignKey("accounts.id"), nullable=True)

    # Relationships
    account = relationship("AccountModel", back_populates="bookmarks")
    quoted_tweet = relationship("TweetModel", remote_side=[rest_id])
