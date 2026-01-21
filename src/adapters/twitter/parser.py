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

            return Tweet(
                rest_id=rest_id,
                text=text,
                author_handle=author_handle,
                author_name=author_name,
                created_at=created_at,
                media_blobs=json.dumps(media_urls),
                raw_data=json.dumps(result),
                quoted_status_id=legacy.get("quoted_status_id_str"),
            )
        except Exception as e:
            # print(f"Failed to parse individual tweet: {e}")
            return None
