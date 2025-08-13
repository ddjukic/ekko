"""
YouTube podcast detector and transcript fetcher for ekko.

This module provides functionality to detect if podcast episodes are available
on YouTube and fetch their transcripts using youtube-transcript-api.
"""

import re
import logging
import os
import sys
from typing import Optional, Tuple, List, Dict, Any

import feedparser

# Add parent directory to path for imports
parent_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)

from models import TranscriptSource, TranscriptResult

logger = logging.getLogger(__name__)


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
    
    def extract_video_id(self, url: str) -> Optional[str]:
        """
        Extract video ID from various YouTube URL formats.
        
        :param url: YouTube video URL
        :type url: str
        
        :return: Video ID if found, None otherwise
        :rtype: Optional[str]
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
        
        :param podcast_name: Name of the podcast
        :type podcast_name: str
        :param episode_title: Title of the episode
        :type episode_title: str
        
        :return: YouTube video URL if found, None otherwise
        :rtype: Optional[str]
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
        Fetch transcript from YouTube video using yt-dlp.
        
        :param video_url: YouTube video URL
        :type video_url: str
        :param languages: List of language codes in order of preference
        :type languages: Optional[List[str]]
        
        :return: TranscriptResult with transcript and metadata
        :rtype: TranscriptResult
        """
        import yt_dlp
        import tempfile
        import os
        
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
            
            # Create temporary directory for subtitle files
            with tempfile.TemporaryDirectory() as temp_dir:
                subtitle_file = os.path.join(temp_dir, f"{video_id}")
                
                # Configure yt-dlp to download subtitles only
                ydl_opts = {
                    'quiet': True,
                    'no_warnings': True,
                    'skip_download': True,  # Don't download video
                    'writesubtitles': True,  # Write subtitles to file
                    'writeautomaticsub': True,  # Also get auto-generated if no manual
                    'subtitleslangs': languages,  # Languages to download
                    'subtitlesformat': 'vtt',  # VTT format is easier to parse
                    'outtmpl': subtitle_file,  # Output template
                    'logger': logger,
                }
                
                logger.info(f"Fetching YouTube transcript for video {video_id}")
                
                with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                    info = ydl.extract_info(video_url, download=True)
                    
                    # Check what subtitle files were created
                    subtitle_files = []
                    source = TranscriptSource.NOT_AVAILABLE
                    quality_score = 0.0
                    
                    # Check for manual subtitles first
                    for lang in languages:
                        manual_file = f"{subtitle_file}.{lang}.vtt"
                        if os.path.exists(manual_file):
                            subtitle_files.append(manual_file)
                            source = TranscriptSource.YOUTUBE_MANUAL
                            quality_score = 1.0
                            logger.info(f"Found manual subtitles for language: {lang}")
                            break
                    
                    # If no manual, check for auto-generated
                    if not subtitle_files:
                        for lang in languages:
                            auto_file = f"{subtitle_file}.{lang}.vtt"
                            if os.path.exists(auto_file):
                                subtitle_files.append(auto_file)
                                source = TranscriptSource.YOUTUBE_AUTO
                                quality_score = 0.8
                                logger.info(f"Found auto-generated subtitles for language: {lang}")
                                break
                    
                    # If we found subtitle files, parse them
                    if subtitle_files:
                        subtitle_text = self._parse_vtt_file(subtitle_files[0])
                        
                        if subtitle_text:
                            word_count = len(subtitle_text.split())
                            
                            metadata = {
                                'video_id': video_id,
                                'video_title': info.get('title', ''),
                                'duration': info.get('duration', 0),
                                'word_count': word_count,
                                'youtube_url': video_url
                            }
                            
                            return TranscriptResult(
                                text=subtitle_text,
                                source=source,
                                quality_score=quality_score,
                                metadata=metadata
                            )
                    
                    # No subtitles found
                    logger.info(f"No subtitles available for video {video_id}")
                    return TranscriptResult(
                        text=None,
                        source=TranscriptSource.NOT_AVAILABLE,
                        quality_score=0.0,
                        metadata={'error': 'No subtitles available', 'video_id': video_id}
                    )
                    
        except Exception as e:
            logger.error(f"Error fetching transcript from YouTube: {e}")
            return TranscriptResult(
                text=None,
                source=TranscriptSource.NOT_AVAILABLE,
                quality_score=0.0,
                metadata={'error': str(e)}
            )
    
    def _parse_vtt_file(self, vtt_file_path: str) -> Optional[str]:
        """
        Parse a VTT subtitle file and extract the text.
        
        :param vtt_file_path: Path to the VTT file
        :type vtt_file_path: str
        
        :return: Extracted text without timestamps
        :rtype: Optional[str]
        """
        try:
            with open(vtt_file_path, 'r', encoding='utf-8') as f:
                lines = f.readlines()
            
            # Skip WEBVTT header and extract only text lines
            text_lines = []
            for line in lines:
                line = line.strip()
                # Skip empty lines, WEBVTT header, and timestamp lines
                if line and not line.startswith('WEBVTT') and '-->' not in line:
                    # Also skip lines that are just numbers (cue identifiers)
                    if not line.isdigit():
                        text_lines.append(line)
            
            # Join all text lines with spaces
            full_text = ' '.join(text_lines)
            
            # Clean up duplicate spaces
            full_text = ' '.join(full_text.split())
            
            return full_text
            
        except Exception as e:
            logger.error(f"Error parsing VTT file: {e}")
            return None
    
    def fetch_transcript_with_timestamps(
        self,
        video_url: str
    ) -> Optional[List[Dict]]:
        """
        Fetch transcript with timestamps for each segment.
        
        .. note::
           This would require parsing VTT files with timestamps preserved.
           Currently not implemented with yt-dlp approach.
        
        :param video_url: YouTube video URL
        :type video_url: str
        
        :return: List of dicts with 'text', 'start', and 'duration' keys
        :rtype: Optional[List[Dict]]
        """
        logger.warning("Transcript with timestamps not implemented with yt-dlp approach")
        return None
    
    def check_youtube_availability(
        self,
        podcast_rss_url: str,
        episode_title: str
    ) -> Tuple[bool, Optional[str]]:
        """
        Check if a podcast episode is available on YouTube.
        
        :param podcast_rss_url: RSS feed URL of the podcast
        :type podcast_rss_url: str
        :param episode_title: Title of the episode
        :type episode_title: str
        
        :return: Tuple of (is_available, youtube_url)
        :rtype: Tuple[bool, Optional[str]]
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
        
        :param transcript: Transcript text
        :type transcript: str
        
        :return: Quality score between 0.0 and 1.0
        :rtype: float
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