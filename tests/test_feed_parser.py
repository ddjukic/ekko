"""
Unit tests for the feed parser module.
"""

import os
import sys
from unittest.mock import MagicMock, patch

import pytest

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from ekko_prototype.models import EpisodeModel
from ekko_prototype.pages.tools.feed_parser import DefaultFeedParserStrategy, FeedParser


class TestFeedParser:
    """Test suite for FeedParser class."""

    @pytest.fixture
    def sample_rss_feed(self):
        """Sample RSS feed content."""
        return """<?xml version="1.0" encoding="UTF-8"?>
        <rss version="2.0" xmlns:itunes="http://www.itunes.com/dtds/podcast-1.0.dtd">
            <channel>
                <title>Test Podcast</title>
                <item>
                    <title>Episode 1: Introduction</title>
                    <guid>ep1-guid</guid>
                    <description>This is the first episode</description>
                    <pubDate>Mon, 01 Jan 2024 00:00:00 GMT</pubDate>
                    <itunes:duration>00:45:30</itunes:duration>
                    <enclosure url="https://example.com/ep1.mp3" type="audio/mpeg"/>
                </item>
                <item>
                    <title>Episode 2: Deep Dive</title>
                    <guid>ep2-guid</guid>
                    <description>This is the second episode</description>
                    <pubDate>Mon, 08 Jan 2024 00:00:00 GMT</pubDate>
                    <itunes:duration>3600</itunes:duration>
                    <enclosure url="https://example.com/ep2.mp3" type="audio/mpeg"/>
                </item>
            </channel>
        </rss>"""

    def test_get_parser_returns_default_strategy(self):
        """Test that get_parser returns DefaultFeedParserStrategy."""
        parser = FeedParser.get_parser("https://example.com/feed.rss")
        assert isinstance(parser, DefaultFeedParserStrategy)

    def test_default_parser_parse_episodes(self, sample_rss_feed):
        """Test DefaultFeedParserStrategy parsing episodes."""
        parser = DefaultFeedParserStrategy()
        episodes = parser.parse(sample_rss_feed)

        assert len(episodes) == 2

        # Check first episode
        ep1 = episodes[0]
        assert isinstance(ep1, EpisodeModel)
        assert ep1.title == "Episode 1: Introduction"
        assert ep1.guid == "ep1-guid"
        assert ep1.description == "This is the first episode"
        assert ep1.audio_url == "https://example.com/ep1.mp3"
        assert ep1.duration == "00:45:30"

        # Check second episode (duration in seconds)
        ep2 = episodes[1]
        assert ep2.title == "Episode 2: Deep Dive"
        assert ep2.duration == "01:00:00"  # Converted from 3600 seconds

    def test_parse_episode_with_missing_fields(self):
        """Test parsing episode with missing optional fields."""
        feed_content = """<?xml version="1.0" encoding="UTF-8"?>
        <rss version="2.0">
            <channel>
                <item>
                    <title>Minimal Episode</title>
                    <guid>minimal-guid</guid>
                </item>
            </channel>
        </rss>"""

        parser = DefaultFeedParserStrategy()
        episodes = parser.parse(feed_content)

        assert len(episodes) == 1
        ep = episodes[0]
        assert ep.title == "Minimal Episode"
        assert ep.guid == "minimal-guid"
        assert ep.audio_url is None
        assert ep.duration is None

    @patch("ekko_prototype.pages.tools.feed_parser.requests.get")
    def test_parse_feed_fetches_and_parses(self, mock_get, sample_rss_feed):
        """Test parse_feed method fetches RSS and parses it."""
        # Mock the HTTP response
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.content = sample_rss_feed.encode("utf-8")
        mock_get.return_value = mock_response

        episodes = FeedParser.parse_feed("https://example.com/feed.rss")

        assert len(episodes) == 2
        assert episodes[0].title == "Episode 1: Introduction"

        # Verify request was made with correct headers
        mock_get.assert_called_once()
        call_args = mock_get.call_args
        assert "User-Agent" in call_args[1]["headers"]

    def test_duration_conversion_from_seconds(self):
        """Test duration conversion from seconds to HH:MM:SS format."""
        feed_content = """<?xml version="1.0" encoding="UTF-8"?>
        <rss version="2.0" xmlns:itunes="http://www.itunes.com/dtds/podcast-1.0.dtd">
            <channel>
                <item>
                    <title>Test Episode</title>
                    <guid>test-guid</guid>
                    <itunes:duration>7265</itunes:duration>
                </item>
            </channel>
        </rss>"""

        parser = DefaultFeedParserStrategy()
        episodes = parser.parse(feed_content)

        assert len(episodes) == 1
        # 7265 seconds = 2 hours, 1 minute, 5 seconds
        assert episodes[0].duration == "02:01:05"

    def test_parse_invalid_feed_content(self):
        """Test parsing invalid feed content."""
        parser = DefaultFeedParserStrategy()

        # Invalid XML
        episodes = parser.parse("not valid xml")
        assert episodes == []

        # Empty content
        episodes = parser.parse("")
        assert episodes == []


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
