from abc import ABC, abstractmethod
from typing import List, Optional
from .entities import Account, Tweet


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
