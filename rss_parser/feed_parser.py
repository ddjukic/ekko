from abc import ABC, abstractmethod
from datetime import datetime

import feedparser


class Episode:
    """Represents a podcast episode."""
    def __init__(self, title, mp3_url, publication_date):
        self.title = title
        self.mp3_url = mp3_url
        self.publication_date = publication_date

class FeedParserStrategy(ABC):
    """Abstract base class for feed parsing strategies."""
    @abstractmethod
    def parse(self, feed_content):
        """Parse the feed content and return a list of Episodes."""
        pass

class DefaultFeedParserStrategy(FeedParserStrategy):
    """Default feed parsing strategy."""
    def parse(self, feed_content):
        parsed_feed = feedparser.parse(feed_content)
        episodes = []
        for entry in parsed_feed.entries:
            title = entry.title
            mp3_url = entry.enclosures[0].href if entry.enclosures else None
            publication_date = datetime(*entry.published_parsed[:6])
            episodes.append(Episode(title, mp3_url, publication_date))
        return episodes