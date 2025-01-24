"""
YouTube podcast detector and transcript fetcher for ekko.

This module provides functionality to detect if podcast episodes are available
on YouTube and fetch their transcripts using youtube-transcript-api.
"""

import re
import logging
from typing import Optional, Tuple, List, Dict
from dataclasses import dataclass
from enum import Enum

import feedparser
from youtube_transcript_api import YouTubeTranscriptApi
from youtube_transcript_api.formatters import TextFormatter

logger = logging.getLogger(__name__)


class TranscriptSource(Enum):
    """Enum representing the source of a transcript."""
    
    YOUTUBE_MANUAL = "youtube_manual"
    YOUTUBE_AUTO = "youtube_auto"
    WHISPER_LOCAL = "whisper_local"
    WHISPER_REMOTE = "whisper_remote"
    NOT_AVAILABLE = "not_available"


@dataclass
class TranscriptResult:
    """Container for transcript fetch results."""
    
    text: Optional[str]
    source: TranscriptSource
    quality_score: float
    metadata: Dict[str, any]


class YouTubePodcastDetector:
    """
    Detect if podcast episodes are available on YouTube and fetch transcripts.
    
    This class provides methods to search for podcast episodes on YouTube
    and extract transcripts when available.
    """
    
    def __init__(self):
        """Initialize the YouTube podcast detector."""
        self.youtube_channels = {
            # Popular podcast YouTube channels
            'The Joe Rogan Experience': 'joerogan',
            'Lex Fridman Podcast': 'lexfridman',
            'The Tim Ferriss Show': 'tim ferriss',
            'Huberman Lab': 'hubermanlab',
            'The Daily': 'nytimes the daily',
            'This American Life': 'this american life',
            'Conan O\'Brien Needs a Friend': 'conan obrien',
            'The Diary Of A CEO': 'steven bartlett',
            'All-In Podcast': 'all in podcast',
            'My First Million': 'my first million',
            "Lenny's Podcast": "Lenny's Podcast",
            "Lennybot": "Lenny's Podcast",
        }
        self.formatter = TextFormatter()
    
    def extract_video_id(self, url: str) -> Optional[str]:
        """
        Extract video ID from various YouTube URL formats.
        
        Args:
            url: YouTube video URL
            
        Returns:
            Video ID if found, None otherwise
        """
        # First check if this is a YouTube URL
        if not any(domain in url.lower() for domain in ['youtube.com', 'youtu.be', 'youtube-nocookie.com']):
            return None
            
        patterns = [
            r'(?:v=|\/)([0-9A-Za-z_-]{11}).*',
            r'(?:embed\/)([0-9A-Za-z_-]{11})',
            r'(?:watch\?v=)([0-9A-Za-z_-]{11})',
            r'(?:youtu\.be\/)([0-9A-Za-z_-]{11})'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, url)
            if match:
                # Extract just the 11-character video ID
                video_id = match.group(1)
                if len(video_id) == 11:
                    return video_id
        return None
    
    def search_youtube_for_episode(
        self,
        podcast_name: str,
        episode_title: str
    ) -> Optional[str]:
        """
        Search YouTube for a specific podcast episode using yt-dlp.
        
        Args:
            podcast_name: Name of the podcast
            episode_title: Title of the episode
            
        Returns:
            YouTube video URL if found, None otherwise
        """
        import yt_dlp
        
        logger.info(f"Searching YouTube for: {podcast_name} - {episode_title}")
        
        # Build search query
        search_query = f"{podcast_name} {episode_title}"
        
        # For known podcasts, add channel info to improve search
        if "lenny" in podcast_name.lower():
            search_query = f"Lenny's Podcast {episode_title}"
        elif podcast_name in self.youtube_channels:
            search_query = f"{self.youtube_channels[podcast_name]} {episode_title}"
        
        # Configure yt-dlp for search only (no download)
        ydl_opts = {
            'quiet': True,
            'no_warnings': True,
            'extract_flat': True,
            'force_generic_extractor': False,
            'default_search': 'ytsearch',
            'max_downloads': 1,
            'logger': logger,
        }
        
        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                # Search for videos (limit to 5 results)
                search_results = ydl.extract_info(f"ytsearch5:{search_query}", download=False)
                
                if search_results and 'entries' in search_results:
                    # Look for best match in results
                    for entry in search_results['entries']:
                        if entry is None:
                            continue
                            
                        video_title = entry.get('title', '').lower()
                        video_url = f"https://www.youtube.com/watch?v={entry.get('id')}"
                        
                        # Check if video title contains key parts of episode title
                        episode_words = episode_title.lower().split()[:5]  # Check first 5 words
                        match_count = sum(1 for word in episode_words if len(word) > 3 and word in video_title)
                        
                        # If we have a good match, return the URL
                        if match_count >= 2 or episode_title.lower()[:30] in video_title:
                            logger.info(f"Found YouTube video: {entry.get('title')} - {video_url}")
                            return video_url
                    
                    # If no good match, return the first result as a fallback for known podcasts
                    if "lenny" in podcast_name.lower() and search_results['entries'][0]:
                        first_result = search_results['entries'][0]
                        video_url = f"https://www.youtube.com/watch?v={first_result.get('id')}"
                        logger.info(f"Using first search result: {first_result.get('title')} - {video_url}")
                        return video_url
                
                logger.info(f"No suitable YouTube video found for: {search_query}")
                return None
                
        except Exception as e:
            logger.error(f"Error searching YouTube: {e}")
            return None
    
    def fetch_youtube_transcript(
        self,
        video_url: str,
        languages: List[str] = None
    ) -> TranscriptResult:
        """
        Fetch transcript from YouTube video.
        
        Args:
            video_url: YouTube video URL
            languages: List of language codes in order of preference
            
        Returns:
            TranscriptResult with transcript and metadata
        """
        if languages is None:
            languages = ['en']
        
        try:
            video_id = self.extract_video_id(video_url)
            if not video_id:
                logger.error(f"Could not extract video ID from URL: {video_url}")
                return TranscriptResult(
                    text=None,
                    source=TranscriptSource.NOT_AVAILABLE,
                    quality_score=0.0,
                    metadata={'error': 'Invalid YouTube URL'}
                )
            
            # Get transcript list
            transcript_list = YouTubeTranscriptApi.list_transcripts(video_id)
            
            # Try to find manual transcript first
            transcript = None
            source = TranscriptSource.NOT_AVAILABLE
            
            try:
                transcript = transcript_list.find_manually_created_transcript(languages)
                source = TranscriptSource.YOUTUBE_MANUAL
                quality_score = 1.0
                logger.info(f"Found manual transcript for video {video_id}")
            except Exception:
                # Fall back to auto-generated
                try:
                    transcript = transcript_list.find_generated_transcript(languages)
                    source = TranscriptSource.YOUTUBE_AUTO
                    quality_score = 0.8
                    logger.info(f"Found auto-generated transcript for video {video_id}")
                except Exception as e:
                    logger.error(f"No transcript available for video {video_id}: {e}")
                    return TranscriptResult(
                        text=None,
                        source=TranscriptSource.NOT_AVAILABLE,
                        quality_score=0.0,
                        metadata={'error': str(e), 'video_id': video_id}
                    )
            
            # Fetch and format transcript
            transcript_data = transcript.fetch()
            
            # Combine all text segments
            full_text = ' '.join([entry['text'] for entry in transcript_data])
            
            # Calculate additional quality metrics
            word_count = len(full_text.split())
            has_timestamps = all('start' in entry for entry in transcript_data)
            
            metadata = {
                'video_id': video_id,
                'language': transcript.language,
                'word_count': word_count,
                'has_timestamps': has_timestamps,
                'segment_count': len(transcript_data)
            }
            
            return TranscriptResult(
                text=full_text,
                source=source,
                quality_score=quality_score,
                metadata=metadata
            )
            
        except Exception as e:
            logger.error(f"Error fetching transcript from YouTube: {e}")
            return TranscriptResult(
                text=None,
                source=TranscriptSource.NOT_AVAILABLE,
                quality_score=0.0,
                metadata={'error': str(e)}
            )
    
    def fetch_transcript_with_timestamps(
        self,
        video_url: str
    ) -> Optional[List[Dict]]:
        """
        Fetch transcript with timestamps for each segment.
        
        Args:
            video_url: YouTube video URL
            
        Returns:
            List of dicts with 'text', 'start', and 'duration' keys
        """
        try:
            video_id = self.extract_video_id(video_url)
            if not video_id:
                return None
            
            transcript = YouTubeTranscriptApi.get_transcript(video_id)
            return transcript
            
        except Exception as e:
            logger.error(f"Error fetching transcript with timestamps: {e}")
            return None
    
    def check_youtube_availability(
        self,
        podcast_rss_url: str,
        episode_title: str
    ) -> Tuple[bool, Optional[str]]:
        """
        Check if a podcast episode is available on YouTube.
        
        Args:
            podcast_rss_url: RSS feed URL of the podcast
            episode_title: Title of the episode
            
        Returns:
            Tuple of (is_available, youtube_url)
        """
        try:
            # Parse RSS feed to get podcast name
            feed = feedparser.parse(podcast_rss_url)
            podcast_name = feed.feed.get('title', '')
            
            # Check if podcast is in known YouTube channels
            if podcast_name in self.youtube_channels:
                youtube_url = self.search_youtube_for_episode(
                    podcast_name,
                    episode_title
                )
                return (youtube_url is not None, youtube_url)
            
            # Try generic search
            youtube_url = self.search_youtube_for_episode(
                podcast_name,
                episode_title
            )
            return (youtube_url is not None, youtube_url)
            
        except Exception as e:
            logger.error(f"Error checking YouTube availability: {e}")
            return (False, None)
    
    def calculate_quality_score(self, transcript: str) -> float:
        """
        Calculate quality score for a transcript.
        
        Args:
            transcript: Transcript text
            
        Returns:
            Quality score between 0.0 and 1.0
        """
        if not transcript:
            return 0.0
        
        score = 1.0
        
        # Check length
        word_count = len(transcript.split())
        if word_count < 500:
            score -= 0.3
        elif word_count < 1000:
            score -= 0.1
        
        # Check for common transcription errors
        if "[inaudible]" in transcript.lower():
            score -= 0.1
        if "[music]" in transcript.lower():
            score -= 0.05
        if transcript.count("...") > 10:
            score -= 0.05
        
        # Check for sentence structure
        sentences = transcript.split('.')
        avg_sentence_length = sum(len(s.split()) for s in sentences) / max(len(sentences), 1)
        if avg_sentence_length < 5 or avg_sentence_length > 30:
            score -= 0.1
        
        return max(0.0, min(1.0, score))