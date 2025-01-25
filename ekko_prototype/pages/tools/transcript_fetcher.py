"""
Unified transcript fetching system for ekko.

This module provides a unified interface for fetching transcripts from various
sources including YouTube and Whisper transcription services.
"""

import logging
import os
import sys
from pathlib import Path

# Add parent directory to path for imports
parent_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)

from models import TranscriptConfig as PydanticTranscriptConfig
from models import TranscriptResult

from .audio_transcriber import EpisodeTranscriber
from .episode_downloader import EpisodeDownloader
from .youtube_detector import TranscriptSource, YouTubePodcastDetector

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


class UnifiedTranscriptFetcher:
    """
    Unified system for fetching transcripts with intelligent fallback.
    
    This class coordinates between YouTube transcript extraction and
    Whisper-based transcription to provide the best available transcript.
    """
    
    def __init__(self, config: PydanticTranscriptConfig | None = None):
        """
        Initialize the unified transcript fetcher.
        
        :param config: Configuration for transcript fetching
        :type config: Optional[PydanticTranscriptConfig]
        """
        self.config = config or PydanticTranscriptConfig()
        self.youtube_detector = YouTubePodcastDetector()
        
        # Only initialize local transcriber if not using OpenAI
        if not self.config.use_openai_whisper:
            self.audio_transcriber = EpisodeTranscriber()
        else:
            self.audio_transcriber = None
            
        self.episode_downloader = EpisodeDownloader('./audio')
        
        # Set up cache directory
        if self.config.cache_transcripts:
            self.cache_dir = Path(self.config.cache_dir)
            self.cache_dir.mkdir(parents=True, exist_ok=True)
    
    def get_transcript(
        self,
        podcast_name: str,
        episode_title: str,
        episode_audio_url: str | None = None,
        podcast_rss_url: str | None = None
    ) -> TranscriptResult:
        """
        Get transcript using intelligent fallback strategy.
        
        Strategy:
        1. Check cache for existing transcript
        2. Try YouTube if available and preferred
        3. Fall back to Whisper transcription
        
        :param podcast_name: Name of the podcast
        :type podcast_name: str
        :param episode_title: Title of the episode
        :type episode_title: str
        :param episode_audio_url: URL of the audio file
        :type episode_audio_url: Optional[str]
        :param podcast_rss_url: RSS feed URL of the podcast
        :type podcast_rss_url: Optional[str]
        
        :return: Transcript result with text and metadata
        :rtype: TranscriptResult
        
        .. note::
           Implements intelligent fallback from free sources (YouTube) 
           to paid sources (Whisper API) to minimize costs.
        """
        # Check cache first
        if self.config.cache_transcripts:
            cached = self._check_cache(podcast_name, episode_title)
            if cached:
                logger.info(f"Found cached transcript for {episode_title}")
                return cached
        
        result = None
        
        # Try YouTube first if preferred
        if self.config.prefer_youtube and podcast_rss_url:
            logger.info("Checking YouTube for transcript...")
            result = self._try_youtube_transcript(
                podcast_rss_url,
                episode_title
            )
        
        # Fall back to Whisper if no YouTube transcript
        if not result or not result.text:
            if episode_audio_url:
                logger.info("Falling back to Whisper transcription...")
                result = self._try_whisper_transcript(
                    episode_audio_url,
                    episode_title,
                    podcast_name
                )
            else:
                logger.error("No audio URL provided for Whisper transcription")
                result = TranscriptResult(
                    text=None,
                    source=TranscriptSource.NOT_AVAILABLE,
                    quality_score=0.0,
                    metadata={'error': 'No audio URL provided'}
                )
        
        # Cache successful result
        if result and result.text and self.config.cache_transcripts:
            self._cache_transcript(podcast_name, episode_title, result)
        
        return result
    
    def _try_youtube_transcript(
        self,
        podcast_rss_url: str,
        episode_title: str
    ) -> TranscriptResult | None:
        """
        Attempt to get transcript from YouTube.
        
        :param podcast_rss_url: RSS feed URL
        :type podcast_rss_url: str
        :param episode_title: Episode title
        :type episode_title: str
        
        :return: TranscriptResult if successful, None otherwise
        :rtype: Optional[TranscriptResult]
        """
        try:
            # Check if episode is on YouTube
            is_available, youtube_url = self.youtube_detector.check_youtube_availability(
                podcast_rss_url,
                episode_title
            )
            
            if is_available and youtube_url:
                logger.info(f"Found YouTube video: {youtube_url}")
                return self.youtube_detector.fetch_youtube_transcript(
                    youtube_url,
                    self.config.youtube_languages
                )
            
            logger.info("Episode not found on YouTube")
            return None
            
        except Exception as e:
            logger.error(f"Error getting YouTube transcript: {e}")
            return None
    
    def _try_whisper_transcript(
        self,
        audio_url: str,
        episode_title: str,
        podcast_name: str
    ) -> TranscriptResult:
        """
        Attempt to transcribe audio using Whisper.
        
        :param audio_url: URL of the audio file
        :type audio_url: str
        :param episode_title: Episode title
        :type episode_title: str
        :param podcast_name: Podcast name
        :type podcast_name: str
        
        :return: TranscriptResult with transcription
        :rtype: TranscriptResult
        """
        try:
            # Download audio file
            logger.info(f"Downloading audio for {episode_title}...")
            logger.debug(f"Audio URL: {audio_url}")
            logger.debug(f"Podcast name: {podcast_name}")
            
            local_audio_path = self.episode_downloader.download_single_episode(
                audio_url,
                episode_title,
                podcast_name
            )
            
            logger.debug(f"Audio downloaded to: {local_audio_path}")
            
            if not local_audio_path:
                raise Exception("Failed to download audio file")
            
            # Transcribe with Whisper
            logger.info(f"Transcribing {episode_title} with Whisper...")
            
            transcript_text = None
            transcript_path = None
            
            if self.config.use_openai_whisper:
                # Use OpenAI Whisper API
                logger.info("Using OpenAI Whisper API for transcription")
                from .openai_whisper_transcriber import OpenAIWhisperTranscriber
                openai_transcriber = OpenAIWhisperTranscriber()
                transcript_text = openai_transcriber.transcribe(
                    local_audio_path,
                    language='en',
                    prompt=f"This is a podcast episode titled '{episode_title}' from {podcast_name}."
                )
                if transcript_text:
                    # Save to file for consistency
                    transcript_path = os.path.join('./transcripts', f"{episode_title}.txt")
                    os.makedirs('./transcripts', exist_ok=True)
                    with open(transcript_path, 'w', encoding='utf-8') as f:
                        f.write(transcript_text)
            elif self.config.use_remote_whisper:
                # Use remote Whisper service via ngrok
                transcript_path = self._transcribe_remote(
                    audio_url,
                    episode_title,
                    podcast_name
                )
                if transcript_path and os.path.exists(transcript_path):
                    with open(transcript_path, encoding='utf-8') as f:
                        transcript_text = f.read()
            else:
                # Use local Whisper
                if self.audio_transcriber:
                    transcript_path = self.audio_transcriber.transcribe(local_audio_path)
                    if transcript_path and os.path.exists(transcript_path):
                        with open(transcript_path, encoding='utf-8') as f:
                            transcript_text = f.read()
                else:
                    logger.error("Local Whisper transcriber not initialized")
                    raise Exception("Local Whisper transcriber not available")
            
            # Check if we got a transcript
            if transcript_text:
                # Calculate quality score
                quality_score = self.youtube_detector.calculate_quality_score(transcript_text)
                
                source = TranscriptSource.WHISPER_LOCAL
                if self.config.use_openai_whisper:
                    source = TranscriptSource.WHISPER_LOCAL  # Consider adding WHISPER_OPENAI
                elif self.config.use_remote_whisper:
                    source = TranscriptSource.WHISPER_REMOTE
                
                return TranscriptResult(
                    text=transcript_text,
                    source=source,
                    quality_score=quality_score,
                    metadata={
                        'audio_file': local_audio_path,
                        'transcript_file': transcript_path,
                        'model': 'whisper-1' if self.config.use_openai_whisper else self.config.whisper_model
                    }
                )
            
            raise Exception("Transcription failed - no output")
            
        except Exception as e:
            logger.error(f"Error transcribing with Whisper: {e}")
            return TranscriptResult(
                text=None,
                source=TranscriptSource.NOT_AVAILABLE,
                quality_score=0.0,
                metadata={'error': str(e)}
            )
    
    def _transcribe_remote(
        self,
        audio_url: str,
        episode_title: str,
        podcast_name: str
    ) -> str | None:
        """
        Transcribe using remote Whisper service.
        
        :param audio_url: URL of the audio file
        :type audio_url: str
        :param episode_title: Episode title
        :type episode_title: str
        :param podcast_name: Podcast name
        :type podcast_name: str
        
        :return: Path to transcript file if successful
        :rtype: Optional[str]
        """
        import requests
        
        # Get configuration from environment
        ngrok_url = os.getenv('NGROK_URL', 'https://internally-next-serval.ngrok-free.app')
        token = os.getenv('TRANSCRIPTION_SERVER_TOKEN', 'chamberOfSecrets')
        
        headers = {"Authorization": f"Bearer {token}"}
        url = f"{ngrok_url}/transcribe"
        data = {
            "episode_url": audio_url,
            "episode_title": episode_title,
            "podcast_title": podcast_name
        }
        
        try:
            response = requests.post(url, headers=headers, json=data, timeout=300)
            
            if response.status_code == 200:
                return response.json().get("transcription_file_path")
            else:
                logger.error(f"Remote transcription failed: {response.status_code}")
                return None
                
        except Exception as e:
            logger.error(f"Error calling remote transcription service: {e}")
            return None
    
    def _check_cache(
        self,
        podcast_name: str,
        episode_title: str
    ) -> TranscriptResult | None:
        """
        Check cache for existing transcript.
        
        :param podcast_name: Podcast name
        :type podcast_name: str
        :param episode_title: Episode title
        :type episode_title: str
        
        :return: Cached TranscriptResult if found
        :rtype: Optional[TranscriptResult]
        """
        if not self.config.cache_transcripts:
            return None
        
        cache_file = self._get_cache_path(podcast_name, episode_title)
        
        if cache_file.exists():
            try:
                import json
                with open(cache_file, encoding='utf-8') as f:
                    data = json.load(f)
                
                return TranscriptResult(
                    text=data['text'],
                    source=TranscriptSource(data['source']),
                    quality_score=data['quality_score'],
                    metadata=data.get('metadata', {})
                )
            except Exception as e:
                logger.error(f"Error reading cache: {e}")
                return None
        
        return None
    
    def _cache_transcript(
        self,
        podcast_name: str,
        episode_title: str,
        result: TranscriptResult
    ) -> None:
        """
        Cache transcript result.
        
        :param podcast_name: Podcast name
        :type podcast_name: str
        :param episode_title: Episode title
        :type episode_title: str
        :param result: TranscriptResult to cache
        :type result: TranscriptResult
        """
        if not self.config.cache_transcripts or not result.text:
            return
        
        cache_file = self._get_cache_path(podcast_name, episode_title)
        
        try:
            import json
            cache_data = {
                'text': result.text,
                'source': result.source.value,
                'quality_score': result.quality_score,
                'metadata': result.metadata
            }
            
            cache_file.parent.mkdir(parents=True, exist_ok=True)
            with open(cache_file, 'w', encoding='utf-8') as f:
                json.dump(cache_data, f, indent=2)
            
            logger.info(f"Cached transcript for {episode_title}")
            
            # Check cache size and clean if needed
            self._manage_cache_size()
            
        except Exception as e:
            logger.error(f"Error caching transcript: {e}")
    
    def _get_cache_path(self, podcast_name: str, episode_title: str) -> Path:
        """
        Get cache file path for a transcript.
        
        :param podcast_name: Podcast name
        :type podcast_name: str
        :param episode_title: Episode title
        :type episode_title: str
        
        :return: Path to cache file
        :rtype: Path
        """
        # Sanitize names for filesystem
        safe_podcast = "".join(c if c.isalnum() or c in " -_" else "_" for c in podcast_name)
        safe_episode = "".join(c if c.isalnum() or c in " -_" else "_" for c in episode_title)
        
        return self.cache_dir / safe_podcast / f"{safe_episode}.json"
    
    def _manage_cache_size(self) -> None:
        """
        Manage cache size by removing old files if needed.
        """
        try:
            # Calculate total cache size
            total_size = sum(f.stat().st_size for f in self.cache_dir.rglob("*.json"))
            max_size = self.config.max_cache_size_mb * 1024 * 1024
            
            if total_size > max_size:
                # Get all cache files sorted by modification time
                cache_files = sorted(
                    self.cache_dir.rglob("*.json"),
                    key=lambda f: f.stat().st_mtime
                )
                
                # Remove oldest files until under limit
                while total_size > max_size and cache_files:
                    oldest = cache_files.pop(0)
                    file_size = oldest.stat().st_size
                    oldest.unlink()
                    total_size -= file_size
                    logger.info(f"Removed old cache file: {oldest.name}")
                    
        except Exception as e:
            logger.error(f"Error managing cache size: {e}")