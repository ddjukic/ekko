import logging
import os
import sys
from abc import ABC, abstractmethod
from datetime import datetime

import feedparser
import requests

# Add parent directory to path for imports
parent_dir = os.path.dirname(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
)
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)

from models import EpisodeModel


class FeedParserStrategy(ABC):
    """
    Abstract base class for feed parsing strategies.
    """

    @abstractmethod
    def parse(self, feed_content: str) -> list[EpisodeModel]:
        """
        Parse the feed content and return a list of Episodes.

        :param feed_content: The raw RSS/XML content of the feed
        :type feed_content: str

        :return: List of parsed episode models
        :rtype: List[EpisodeModel]
        """
        pass


class DefaultFeedParserStrategy(FeedParserStrategy):
    """
    Default feed parsing strategy using feedparser library.
    """

    def parse(self, feed_content: str) -> list[EpisodeModel]:
        """
        Parse the default feed content to extract episode information.

        :param feed_content: The RSS/XML content to parse
        :type feed_content: str

        :return: List of episode models extracted from the feed
        :rtype: List[EpisodeModel]

        .. note::
           Handles iTunes-specific fields like itunes_duration, itunes_season, etc.
        """
        parsed_feed = feedparser.parse(feed_content)
        episodes = []
        for entry in parsed_feed.entries:
            try:
                # Extract basic fields
                title = entry.get("title", "")
                audio_url = entry.enclosures[0].href if entry.enclosures else None

                # Parse publication date
                published_date = None
                if hasattr(entry, "published_parsed") and entry.published_parsed:
                    published_date = datetime(*entry.published_parsed[:6])

                # Extract duration
                duration = None
                if hasattr(entry, "itunes_duration"):
                    duration = entry.itunes_duration
                    # Convert to HH:MM:SS if it's in seconds
                    if duration and ":" not in str(duration):
                        try:
                            seconds = int(duration)
                            hours = seconds // 3600
                            minutes = (seconds % 3600) // 60
                            secs = seconds % 60
                            duration = f"{hours:02d}:{minutes:02d}:{secs:02d}"
                        except (ValueError, TypeError):
                            pass

                # Create EpisodeModel
                episode = EpisodeModel(
                    guid=entry.get("guid", entry.get("id", title)),
                    title=title,
                    description=entry.get("summary", entry.get("description")),
                    published_date=published_date,
                    duration=duration,
                    audio_url=audio_url,
                    transcript_url=entry.get("transcript_url"),
                    image=entry.get("image", {}).get("href")
                    if hasattr(entry, "image")
                    else None,
                    season=entry.get("itunes_season"),
                    episode_number=entry.get("itunes_episode"),
                )
                episodes.append(episode)
            except Exception as e:
                logging.warning(f"Error parsing episode entry: {e}")
                continue
        return episodes


class FeedParser:
    """
    An RSS feed parser factory which gets the appropriate feed parser based on the feed content.
    """

    @staticmethod
    def get_parser(feed_url: str) -> FeedParserStrategy:
        """
        Get the appropriate parser for the feed.

        :param feed_url: The URL of the feed
        :type feed_url: str

        :return: An instance of a feed parser strategy
        :rtype: FeedParserStrategy

        .. note::
           Currently always returns DefaultFeedParserStrategy.
           Future versions may select different strategies based on feed type.
        """
        # Placeholder for future logic to determine the parser
        return DefaultFeedParserStrategy()

    @staticmethod
    def parse_feed(feed_url: str) -> list[EpisodeModel]:
        """
        Fetch and parse the podcast feed.

        :param feed_url: The URL of the podcast RSS feed
        :type feed_url: str

        :return: List of episode models parsed from the feed
        :rtype: List[EpisodeModel]

        :raises requests.RequestException: If feed cannot be fetched
        """
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.5",
            "DNT": "1",
            "Connection": "keep-alive",
            "Upgrade-Insecure-Requests": "1",
        }
        response = requests.get(feed_url, headers=headers)

        # Log only basic info, not the entire feed content
        import logging

        logger = logging.getLogger(__name__)
        logger.debug(
            f"Fetched RSS feed from {feed_url}, status: {response.status_code}, size: {len(response.content)} bytes"
        )

        parser = FeedParser.get_parser(feed_url)
        return parser.parse(response.content)
