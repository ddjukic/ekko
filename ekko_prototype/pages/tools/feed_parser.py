import feedparser
from datetime import datetime
from abc import ABC, abstractmethod
from datetime import timedelta
import requests

class Episode:
    """Represents a podcast episode.

    Attributes:
        title (str): The title of the episode.
        mp3_url (str): The URL to the episode's MP3 file.
        publication_date (datetime): The publication date of the episode.
    """
    def __init__(self, title, mp3_url, publication_date, duration=None):
        self.title = title
        self.mp3_url = mp3_url
        self.publication_date = publication_date
        self.duration = duration

class FeedParserStrategy(ABC):
    """Abstract base class for feed parsing strategies."""
    @abstractmethod
    def parse(self, feed_content):
        """Parse the feed content and return a list of Episodes.

        Args:
            feed_content (str): The content of the feed to be parsed.

        Returns:
            list: A list of Episode instances.
        """
        pass

class DefaultFeedParserStrategy(FeedParserStrategy):
    """Default feed parsing strategy."""
    def parse(self, feed_content):
        """Parse the default feed content to extract episode information.

        Args:
            feed_content (str): The content of the feed to be parsed.

        Returns:
            list: A list of Episode instances.
        """
        parsed_feed = feedparser.parse(feed_content)
        episodes = []
        for entry in parsed_feed.entries:
            title = entry.title
            mp3_url = entry.enclosures[0].href if entry.enclosures else None
            publication_date = datetime(*entry.published_parsed[:6])
            duration = entry.itunes_duration if hasattr(entry, 'itunes_duration') else None
            # duration is in seconds; convert to HH:MM:SS format
            if duration:
                try:
                    # this is for the case where duration is in the format of raw seconds
                    duration = str(timedelta(seconds=int(duration)))
                    # otherwise; parse the duration as a string
                except:
                    duration = duration
            episodes.append(Episode(title, mp3_url, publication_date, duration))
        return episodes

class FeedParser:
    """An RSS feed parser factory which gets the appropriate feed parser based on the feed content."""
    @staticmethod
    def get_parser(feed_url):
        """Get the appropriate parser for the feed.

        Args:
            feed_url (str): The URL of the feed.

        Returns:
            FeedParserStrategy: An instance of a feed parser strategy.
        """
        # Placeholder for future logic to determine the parser
        return DefaultFeedParserStrategy()

    @staticmethod
    def parse_feed(feed_url):
        """Fetch and parse the podcast feed.

        Args:
            feed_url (str): The URL of the podcast feed.

        Returns:
            list: A list of Episode instances parsed from the feed.
        """
        headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.5',
        'DNT': '1',
        'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
        }
        response = requests.get(feed_url, headers=headers)

        # Log only basic info, not the entire feed content
        import logging
        logger = logging.getLogger(__name__)
        logger.debug(f"Fetched RSS feed from {feed_url}, status: {response.status_code}, size: {len(response.content)} bytes")

        parser = FeedParser.get_parser(feed_url)
        return parser.parse(response.content)