"""
Unit tests for YouTube transcript detection and fetching.
"""

import os
import sys
import unittest
from unittest.mock import MagicMock, Mock, patch

# Add the parent directory to the path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from ekko_prototype.pages.tools.youtube_detector import (
    TranscriptSource,
    YouTubePodcastDetector,
)


class TestYouTubeDetector(unittest.TestCase):
    """Test YouTube transcript detection and fetching."""

    def setUp(self):
        """Set up test fixtures."""
        self.detector = YouTubePodcastDetector()

    def test_extract_video_id_standard_url(self):
        """Test extracting video ID from standard YouTube URL."""
        url = "https://www.youtube.com/watch?v=dQw4w9WgXcQ"
        video_id = self.detector.extract_video_id(url)
        self.assertEqual(video_id, "dQw4w9WgXcQ")

    def test_extract_video_id_short_url(self):
        """Test extracting video ID from shortened YouTube URL."""
        url = "https://youtu.be/dQw4w9WgXcQ"
        video_id = self.detector.extract_video_id(url)
        self.assertEqual(video_id, "dQw4w9WgXcQ")

    def test_extract_video_id_embed_url(self):
        """Test extracting video ID from embedded YouTube URL."""
        url = "https://www.youtube.com/embed/dQw4w9WgXcQ"
        video_id = self.detector.extract_video_id(url)
        self.assertEqual(video_id, "dQw4w9WgXcQ")

    def test_extract_video_id_invalid_url(self):
        """Test extracting video ID from invalid URL returns None."""
        url = "https://example.com/not-a-youtube-url"
        video_id = self.detector.extract_video_id(url)
        self.assertIsNone(video_id)

    @patch("yt_dlp.YoutubeDL")
    def test_search_youtube_for_episode_success(self, mock_ydl_class):
        """Test successful YouTube search for podcast episode."""
        # Mock the YoutubeDL instance
        mock_ydl = MagicMock()
        mock_ydl_class.return_value.__enter__.return_value = mock_ydl

        # Mock search results - use valid 11-character video ID
        mock_results = {
            "entries": [
                {
                    "id": "dQw4w9WgXcQ",  # Valid 11-character YouTube ID
                    "title": "Inside ChatGPT with Nick Turley - Lenny's Podcast",
                }
            ]
        }
        mock_ydl.extract_info.return_value = mock_results

        # Test the search
        result = self.detector.search_youtube_for_episode(
            "Lenny's Podcast",
            "Inside ChatGPT: The fastest growing product in history | Nick Turley",
        )

        # Verify the result
        self.assertEqual(result, "https://www.youtube.com/watch?v=dQw4w9WgXcQ")
        mock_ydl.extract_info.assert_called_once()

    @patch("yt_dlp.YoutubeDL")
    def test_search_youtube_for_episode_no_results(self, mock_ydl_class):
        """Test YouTube search with no results."""
        # Mock the YoutubeDL instance
        mock_ydl = MagicMock()
        mock_ydl_class.return_value.__enter__.return_value = mock_ydl

        # Mock empty search results
        mock_results = {"entries": []}
        mock_ydl.extract_info.return_value = mock_results

        # Test the search
        result = self.detector.search_youtube_for_episode(
            "Unknown Podcast", "Unknown Episode"
        )

        # Verify no result
        self.assertIsNone(result)

    @patch("ekko_prototype.pages.tools.youtube_detector.YouTubeTranscriptApi")
    def test_fetch_youtube_transcript_success(self, mock_api):
        """Test successful transcript fetching from YouTube."""
        # Mock transcript data
        mock_transcript = Mock()
        mock_transcript.fetch.return_value = [
            {"text": "Hello world", "start": 0.0, "duration": 2.0},
            {"text": "This is a test", "start": 2.0, "duration": 2.0},
        ]
        mock_transcript.language = "en"

        # Mock transcript list
        mock_transcript_list = Mock()
        mock_transcript_list.find_manually_created_transcript.return_value = (
            mock_transcript
        )
        mock_api.list_transcripts.return_value = mock_transcript_list

        # Test fetching transcript - use valid 11-character video ID
        result = self.detector.fetch_youtube_transcript(
            "https://www.youtube.com/watch?v=dQw4w9WgXcQ"  # Valid 11-character ID
        )

        # Verify the result
        self.assertIsNotNone(result)
        self.assertEqual(result.source, TranscriptSource.YOUTUBE_MANUAL)
        self.assertEqual(result.text, "Hello world This is a test")
        self.assertGreater(result.quality_score, 0.5)
        self.assertEqual(result.metadata["video_id"], "dQw4w9WgXcQ")

    @patch("ekko_prototype.pages.tools.youtube_detector.YouTubeTranscriptApi")
    def test_fetch_youtube_transcript_auto_generated(self, mock_api):
        """Test fetching auto-generated transcript when manual is not available."""
        # Mock transcript data
        mock_transcript = Mock()
        mock_transcript.fetch.return_value = [
            {"text": "Auto generated text", "start": 0.0, "duration": 2.0}
        ]
        mock_transcript.language = "en"

        # Mock transcript list - manual not found, auto-generated available
        mock_transcript_list = Mock()
        mock_transcript_list.find_manually_created_transcript.side_effect = Exception(
            "No manual transcript"
        )
        mock_transcript_list.find_generated_transcript.return_value = mock_transcript
        mock_api.list_transcripts.return_value = mock_transcript_list

        # Test fetching transcript - use valid 11-character video ID
        result = self.detector.fetch_youtube_transcript(
            "https://www.youtube.com/watch?v=dQw4w9WgXcQ"
        )

        # Verify the result
        self.assertIsNotNone(result)
        self.assertEqual(result.source, TranscriptSource.YOUTUBE_AUTO)
        self.assertEqual(result.text, "Auto generated text")
        self.assertEqual(result.quality_score, 0.8)  # Auto-generated gets 0.8

    @patch("ekko_prototype.pages.tools.youtube_detector.YouTubeTranscriptApi")
    def test_fetch_youtube_transcript_not_available(self, mock_api):
        """Test handling when no transcript is available."""
        # Mock transcript list - no transcripts available
        mock_transcript_list = Mock()
        mock_transcript_list.find_manually_created_transcript.side_effect = Exception(
            "No manual transcript"
        )
        mock_transcript_list.find_generated_transcript.side_effect = Exception(
            "No auto transcript"
        )
        mock_api.list_transcripts.return_value = mock_transcript_list

        # Test fetching transcript - use valid 11-character video ID
        result = self.detector.fetch_youtube_transcript(
            "https://www.youtube.com/watch?v=dQw4w9WgXcQ"
        )

        # Verify the result
        self.assertIsNotNone(result)
        self.assertEqual(result.source, TranscriptSource.NOT_AVAILABLE)
        self.assertIsNone(result.text)
        self.assertEqual(result.quality_score, 0.0)

    @patch("ekko_prototype.pages.tools.youtube_detector.feedparser")
    def test_check_youtube_availability(self, mock_feedparser):
        """Test checking if episode is available on YouTube."""
        # Mock RSS feed
        mock_feed = Mock()
        mock_feed.feed = {"title": "Lenny's Podcast"}
        mock_feedparser.parse.return_value = mock_feed

        # Mock successful YouTube search - use valid 11-character video ID
        with patch.object(self.detector, "search_youtube_for_episode") as mock_search:
            mock_search.return_value = "https://www.youtube.com/watch?v=dQw4w9WgXcQ"

            is_available, url = self.detector.check_youtube_availability(
                "https://example.com/feed.rss", "Test Episode"
            )

            self.assertTrue(is_available)
            self.assertEqual(url, "https://www.youtube.com/watch?v=dQw4w9WgXcQ")

    def test_calculate_quality_score(self):
        """Test transcript quality score calculation."""
        # Test with good quality transcript
        good_transcript = (
            "This is a high quality transcript with proper sentences. " * 100
        )
        score = self.detector.calculate_quality_score(good_transcript)
        self.assertGreater(score, 0.8)

        # Test with poor quality transcript
        poor_transcript = "short text"
        score = self.detector.calculate_quality_score(poor_transcript)
        self.assertLess(score, 0.7)

        # Test with transcript containing errors
        error_transcript = "[inaudible] some text [music] ... " * 50
        score = self.detector.calculate_quality_score(error_transcript)
        self.assertLess(score, 0.8)

        # Test with None transcript
        score = self.detector.calculate_quality_score(None)
        self.assertEqual(score, 0.0)


if __name__ == "__main__":
    unittest.main()
