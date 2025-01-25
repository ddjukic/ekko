#!/usr/bin/env python3
"""
Integration test for transcript fetching with OpenAI Whisper.
"""

import logging
import os
import sys

# Add project paths
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from ekko_prototype.models import TranscriptConfig
from ekko_prototype.pages.tools.transcript_fetcher import UnifiedTranscriptFetcher
from ekko_prototype.pages.tools.youtube_detector import TranscriptSource

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def test_transcript_fetching():
    """Test the transcript fetching system."""
    
    # Configure to use OpenAI Whisper
    config = TranscriptConfig(
        prefer_youtube=True,
        use_openai_whisper=True,  # Use OpenAI Whisper API
        use_remote_whisper=False,
        cache_transcripts=True
    )
    
    fetcher = UnifiedTranscriptFetcher(config)
    
    # Test with a Lenny's Podcast episode
    podcast_name = "Lenny's Podcast"
    episode_title = "How Canva grows: Lessons from 150M users | Cameron Adams (Co-founder, Chief Product Officer)"
    episode_audio_url = "https://anchor.fm/s/a0419834/podcast/play/95432635/https%3A%2F%2Fd3ctxlq1ktw2nl.cloudfront.net%2Fstaging%2F2024-11-27%2F64c0f65b-e847-a1be-d7f0-5d2c0c12e436.mp3"
    podcast_rss_url = "https://anchor.fm/s/a0419834/podcast/rss"
    
    logger.info(f"Testing transcript fetch for: {episode_title}")
    
    try:
        result = fetcher.get_transcript(
            podcast_name=podcast_name,
            episode_title=episode_title,
            episode_audio_url=episode_audio_url,
            podcast_rss_url=podcast_rss_url
        )
        
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
            elif result.source == TranscriptSource.WHISPER_LOCAL:
                logger.info("✅ Got transcript from Whisper (OpenAI or local)")
                if result.metadata.get('model') == 'whisper-1':
                    logger.info("✅ Used OpenAI Whisper API")
            
            return True
        else:
            logger.error("❌ Failed to fetch transcript")
            if result:
                logger.error(f"Source: {result.source.value}")
                logger.error(f"Metadata: {result.metadata}")
            return False
            
    except Exception as e:
        logger.exception(f"❌ Error during transcript fetching: {e}")
        return False

if __name__ == "__main__":
    success = test_transcript_fetching()
    sys.exit(0 if success else 1)