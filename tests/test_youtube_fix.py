#!/usr/bin/env python3
"""
Test the fixed YouTube transcript fetching with yt-dlp.
"""

import logging
import os
import sys

# Add project paths
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from ekko_prototype.pages.tools.youtube_detector import (
    TranscriptSource,
    YouTubePodcastDetector,
)

# Set up logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


def test_youtube_transcript():
    """Test YouTube transcript fetching with a real video."""

    detector = YouTubePodcastDetector()

    # Test with a Lenny's Podcast episode that should have transcripts
    test_url = "https://www.youtube.com/watch?v=dQw4w9WgXcQ"  # Rick Astley - should have subtitles

    logger.info(f"Testing YouTube transcript fetch for: {test_url}")

    result = detector.fetch_youtube_transcript(test_url)

    if result and result.text:
        logger.info("✅ Successfully fetched transcript!")
        logger.info(f"Source: {result.source.value}")
        logger.info(f"Quality score: {result.quality_score:.2f}")
        logger.info(f"Text length: {len(result.text)} characters")
        logger.info(f"First 200 chars: {result.text[:200]}...")

        if result.source == TranscriptSource.YOUTUBE_MANUAL:
            logger.info("✅ Got YouTube manual transcript (best quality)")
        elif result.source == TranscriptSource.YOUTUBE_AUTO:
            logger.info("✅ Got YouTube auto-generated transcript")

        return True
    else:
        logger.error("❌ Failed to fetch transcript")
        if result:
            logger.error(f"Source: {result.source.value}")
            logger.error(f"Metadata: {result.metadata}")
        return False


if __name__ == "__main__":
    success = test_youtube_transcript()
    sys.exit(0 if success else 1)
