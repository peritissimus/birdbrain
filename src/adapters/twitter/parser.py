import json
from datetime import datetime
from typing import List, Optional, Dict, Any
from src.core.entities import Tweet


class TwitterParser:
    @staticmethod
    def parse_bookmarks_response(response_json: Dict[str, Any]) -> List[Tweet]:
        """
        Parses the 'Bookmark' GraphQL response.
        Expected structure varies, but generally:
        data -> bookmark_timeline_v2 -> timeline -> instructions -> entries -> content -> itemContent -> tweet_results -> result
        """
        tweets = []

        try:
            instructions = (
                response_json.get("data", {})
                .get("bookmark_timeline_v2", {})
                .get("timeline", {})
                .get("instructions", [])
            )

            for instruction in instructions:
                if instruction.get("type") == "TimelineAddEntries":
                    for entry in instruction.get("entries", []):
                        tweet_data = TwitterParser._extract_tweet_from_entry(entry)
                        if tweet_data:
                            tweets.append(tweet_data)
        except Exception as e:
            # In a real app, log this error
            print(f"Error parsing response: {e}")
            pass

        return tweets

    @staticmethod
    def _extract_tweet_from_entry(entry: Dict[str, Any]) -> Optional[Tweet]:
        try:
            content = entry.get("content", {})
            if content.get("entryType") != "TimelineTimelineItem":
                return None

            result = (
                content.get("itemContent", {})
                .get("tweet_results", {})
                .get("result", {})
            )

            # Handle Retweets / Notes / etc.
            if "tweet" in result:
                # This happens sometimes with legacy or extended structures
                result = result["tweet"]

            if not result or "legacy" not in result:
                return None

            legacy = result["legacy"]
            core = result.get("core", {}).get("user_results", {}).get("result", {})

            rest_id = result.get("rest_id")

            # Text extraction strategy: Note Tweet > Legacy Full Text
            text = legacy.get("full_text")
            note_tweet = result.get("note_tweet", {})
            if note_tweet.get("is_expandable"):
                try:
                    note_text = note_tweet["note_tweet_results"]["result"]["text"]
                    if note_text:
                        text = note_text
                except (KeyError, TypeError):
                    pass

            created_at_str = legacy.get(
                "created_at"
            )  # "Fri Dec 06 10:37:37 +0000 2024"

            # Parse Date
            # Python's strptime %z handles +0000
            created_at = datetime.strptime(created_at_str, "%a %b %d %H:%M:%S %z %Y")

            # Try to find user info in legacy (old style) or core (new style)
            user_legacy = core.get("legacy", {})
            user_core = core.get("core", {})

            author_handle = user_legacy.get("screen_name")
            if not author_handle:
                author_handle = user_core.get("screen_name", "unknown")

            author_name = user_legacy.get("name")
            if not author_name:
                author_name = user_core.get("name", "unknown")

            # Media
            media_urls = []
            if "extended_entities" in legacy and "media" in legacy["extended_entities"]:
                for m in legacy["extended_entities"]["media"]:
                    media_urls.append(m.get("media_url_https"))

            # Detect truncation
            is_truncated = legacy.get("truncated", False)
            if not is_truncated and text:
                # Also check if text ends with ellipsis (common truncation indicator)
                is_truncated = text.rstrip().endswith("…") or text.rstrip().endswith("...")

            # Check if quoted tweet data is missing
            quoted_status_id = legacy.get("quoted_status_id_str")
            is_quote_missing = bool(quoted_status_id) and not result.get("quoted_status_result")

            # Needs hydration if truncated or quote is missing
            needs_hydration = is_truncated or is_quote_missing

            return Tweet(
                rest_id=rest_id,
                text=text,
                author_handle=author_handle,
                author_name=author_name,
                created_at=created_at,
                media_blobs=json.dumps(media_urls),
                raw_data=json.dumps(result),
                quoted_status_id=quoted_status_id,
                is_truncated=is_truncated,
                is_quote_missing=is_quote_missing,
                needs_hydration=needs_hydration,
            )
        except Exception as e:
            # print(f"Failed to parse individual tweet: {e}")
            return None

    @staticmethod
    def parse_tweet_detail(response_json: Dict[str, Any]) -> Optional[Tweet]:
        """
        Parse a TweetDetail GraphQL response (when viewing a single tweet).
        Structure: data -> tweetResult -> result
        """
        try:
            result = (
                response_json.get("data", {})
                .get("tweetResult", {})
                .get("result", {})
            )

            if not result:
                # Try alternate structure
                result = response_json.get("data", {}).get("tweet", {}).get("result", {})

            if not result or "legacy" not in result:
                return None

            return TwitterParser._parse_tweet_result(result)
        except Exception as e:
            print(f"Error parsing tweet detail: {e}")
            return None

    @staticmethod
    def extract_quoted_tweet(response_json: Dict[str, Any]) -> Optional[Tweet]:
        """
        Extract the quoted tweet from a TweetDetail response.
        """
        try:
            result = (
                response_json.get("data", {})
                .get("tweetResult", {})
                .get("result", {})
            )

            if not result:
                result = response_json.get("data", {}).get("tweet", {}).get("result", {})

            quoted_result = result.get("quoted_status_result", {}).get("result", {})
            if not quoted_result or "legacy" not in quoted_result:
                return None

            return TwitterParser._parse_tweet_result(quoted_result)
        except Exception as e:
            print(f"Error extracting quoted tweet: {e}")
            return None

    @staticmethod
    def _parse_tweet_result(result: Dict[str, Any]) -> Optional[Tweet]:
        """Parse a tweet result object into a Tweet entity."""
        try:
            if "tweet" in result:
                result = result["tweet"]

            legacy = result["legacy"]
            core = result.get("core", {}).get("user_results", {}).get("result", {})

            rest_id = result.get("rest_id")

            # Text extraction: Note Tweet > Legacy Full Text
            text = legacy.get("full_text")
            note_tweet = result.get("note_tweet", {})
            if note_tweet.get("is_expandable"):
                try:
                    note_text = note_tweet["note_tweet_results"]["result"]["text"]
                    if note_text:
                        text = note_text
                except (KeyError, TypeError):
                    pass

            created_at_str = legacy.get("created_at")
            created_at = datetime.strptime(created_at_str, "%a %b %d %H:%M:%S %z %Y")

            user_legacy = core.get("legacy", {})
            author_handle = user_legacy.get("screen_name", "unknown")
            author_name = user_legacy.get("name", "unknown")

            media_urls = []
            if "extended_entities" in legacy and "media" in legacy["extended_entities"]:
                for m in legacy["extended_entities"]["media"]:
                    media_urls.append(m.get("media_url_https"))

            quoted_status_id = legacy.get("quoted_status_id_str")
            is_truncated = legacy.get("truncated", False)
            is_quote_missing = bool(quoted_status_id) and not result.get("quoted_status_result")
            needs_hydration = is_truncated or is_quote_missing

            return Tweet(
                rest_id=rest_id,
                text=text,
                author_handle=author_handle,
                author_name=author_name,
                created_at=created_at,
                media_blobs=json.dumps(media_urls),
                raw_data=json.dumps(result),
                quoted_status_id=quoted_status_id,
                is_truncated=is_truncated,
                is_quote_missing=is_quote_missing,
                needs_hydration=needs_hydration,
            )
        except Exception as e:
            print(f"Error parsing tweet result: {e}")
            return None
