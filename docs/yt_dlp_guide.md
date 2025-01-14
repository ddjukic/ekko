# YouTube Transcript Extraction Guide for ekko

## Overview

This guide covers methods for extracting transcripts from YouTube videos, which can be used when podcasts are also available on YouTube.

## Primary Method: youtube-transcript-api

The `youtube-transcript-api` is the simplest and most efficient method for transcript extraction.

### Installation

```bash
uv add youtube-transcript-api
```

### Basic Usage

```python
from youtube_transcript_api import YouTubeTranscriptApi
from typing import Optional, List, Dict

def get_youtube_video_id(url: str) -> Optional[str]:
    """Extract video ID from YouTube URL."""
    import re
    patterns = [
        r'(?:v=|\/)([0-9A-Za-z_-]{11}).*',
        r'(?:embed\/)([0-9A-Za-z_-]{11})',
        r'(?:watch\?v=)([0-9A-Za-z_-]{11})',
        r'(?:youtu\.be\/)([0-9A-Za-z_-]{11})'
    ]
    
    for pattern in patterns:
        match = re.search(pattern, url)
        if match:
            return match.group(1)
    return None

def fetch_youtube_transcript(
    video_url: str, 
    languages: List[str] = ['en']
) -> Optional[str]:
    """
    Fetch transcript from YouTube video.
    
    Args:
        video_url: YouTube video URL
        languages: List of language codes in order of preference
        
    Returns:
        Transcript text or None if not available
    """
    try:
        video_id = get_youtube_video_id(video_url)
        if not video_id:
            return None
            
        # Get transcript list
        transcript_list = YouTubeTranscriptApi.list_transcripts(video_id)
        
        # Try to find manual transcript first
        try:
            transcript = transcript_list.find_manually_created_transcript(languages)
        except:
            # Fall back to auto-generated
            transcript = transcript_list.find_generated_transcript(languages)
        
        # Fetch and format transcript
        transcript_data = transcript.fetch()
        
        # Combine all text segments
        full_text = ' '.join([entry['text'] for entry in transcript_data])
        
        return full_text
        
    except Exception as e:
        print(f"Error fetching transcript: {e}")
        return None

def fetch_transcript_with_timestamps(
    video_url: str
) -> Optional[List[Dict]]:
    """
    Fetch transcript with timestamps for each segment.
    
    Returns:
        List of dicts with 'text', 'start', and 'duration' keys
    """
    try:
        video_id = get_youtube_video_id(video_url)
        if not video_id:
            return None
            
        transcript = YouTubeTranscriptApi.get_transcript(video_id)
        return transcript
        
    except Exception as e:
        print(f"Error fetching transcript: {e}")
        return None
```

### Advanced Features

```python
from youtube_transcript_api.formatters import TextFormatter, JSONFormatter

def format_transcript(transcript_data: List[Dict], format_type: str = 'text') -> str:
    """
    Format transcript data in various formats.
    
    Args:
        transcript_data: Raw transcript data
        format_type: 'text' or 'json'
    """
    if format_type == 'json':
        formatter = JSONFormatter()
    else:
        formatter = TextFormatter()
    
    return formatter.format_transcript(transcript_data)

def translate_transcript(
    video_url: str,
    target_language: str = 'es'
) -> Optional[str]:
    """
    Fetch and translate transcript to target language.
    """
    try:
        video_id = get_youtube_video_id(video_url)
        if not video_id:
            return None
            
        transcript_list = YouTubeTranscriptApi.list_transcripts(video_id)
        
        # Get any available transcript
        transcript = transcript_list.find_transcript(['en'])
        
        # Translate
        translated = transcript.translate(target_language)
        translated_data = translated.fetch()
        
        return ' '.join([entry['text'] for entry in translated_data])
        
    except Exception as e:
        print(f"Error translating transcript: {e}")
        return None
```

## Alternative Method: yt-dlp

For more complex scenarios or when you need video/audio along with transcripts.

### Installation

```bash
uv add yt-dlp
```

### Usage for Subtitle Extraction

```python
import yt_dlp
import os
from typing import Optional

def extract_subtitles_with_ytdlp(
    video_url: str,
    output_dir: str = './transcripts'
) -> Optional[str]:
    """
    Extract subtitles using yt-dlp.
    
    Args:
        video_url: YouTube video URL
        output_dir: Directory to save subtitle files
        
    Returns:
        Path to subtitle file or None
    """
    os.makedirs(output_dir, exist_ok=True)
    
    ydl_opts = {
        'writesubtitles': True,
        'writeautomaticsub': True,  # Get auto-generated if manual not available
        'subtitlesformat': 'vtt',  # or 'srt'
        'skip_download': True,  # Don't download video
        'outtmpl': f'{output_dir}/%(title)s.%(ext)s',
        'quiet': True,
        'no_warnings': True,
    }
    
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(video_url, download=True)
            video_title = info.get('title', 'video')
            
            # Check for subtitle file
            subtitle_file = f"{output_dir}/{video_title}.en.vtt"
            if os.path.exists(subtitle_file):
                return subtitle_file
                
    except Exception as e:
        print(f"Error extracting subtitles: {e}")
        
    return None

def parse_vtt_file(vtt_file_path: str) -> str:
    """
    Parse VTT subtitle file to extract plain text.
    """
    import re
    
    with open(vtt_file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Remove WEBVTT header and timestamps
    lines = content.split('\n')
    text_lines = []
    
    for line in lines:
        # Skip timestamps (contain -->)
        if '-->' in line:
            continue
        # Skip WEBVTT header
        if line.startswith('WEBVTT'):
            continue
        # Skip empty lines
        if line.strip():
            # Clean HTML tags if present
            clean_line = re.sub('<[^>]+>', '', line)
            text_lines.append(clean_line.strip())
    
    return ' '.join(text_lines)
```

## Integration with ekko

### YouTube Podcast Detector

```python
import re
from typing import Optional, Tuple

class YouTubePodcastDetector:
    """Detect if a podcast episode is available on YouTube."""
    
    def __init__(self):
        self.youtube_channels = {
            # Map podcast names to YouTube channel IDs or search terms
            'The Joe Rogan Experience': 'joerogan',
            'Lex Fridman Podcast': 'lexfridman',
            'The Tim Ferriss Show': 'tim ferriss',
            # Add more podcast mappings
        }
    
    def search_youtube_for_episode(
        self,
        podcast_name: str,
        episode_title: str
    ) -> Optional[str]:
        """
        Search YouTube for a specific podcast episode.
        
        Returns:
            YouTube video URL if found, None otherwise
        """
        # Implementation would use YouTube Data API
        # or yt-dlp search functionality
        search_query = f"{podcast_name} {episode_title}"
        
        ydl_opts = {
            'quiet': True,
            'no_warnings': True,
            'extract_flat': True,
            'force_generic_extractor': False,
        }
        
        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                result = ydl.extract_info(
                    f"ytsearch1:{search_query}", 
                    download=False
                )
                
                if result and 'entries' in result and result['entries']:
                    video = result['entries'][0]
                    return f"https://www.youtube.com/watch?v={video['id']}"
                    
        except Exception as e:
            print(f"Error searching YouTube: {e}")
            
        return None
    
    def check_youtube_availability(
        self,
        podcast_rss_url: str,
        episode_title: str
    ) -> Tuple[bool, Optional[str]]:
        """
        Check if episode is available on YouTube.
        
        Returns:
            Tuple of (is_available, youtube_url)
        """
        # Extract podcast name from RSS URL or metadata
        podcast_name = self._extract_podcast_name(podcast_rss_url)
        
        if podcast_name in self.youtube_channels:
            youtube_url = self.search_youtube_for_episode(
                podcast_name, 
                episode_title
            )
            return (youtube_url is not None, youtube_url)
            
        return (False, None)
    
    def _extract_podcast_name(self, rss_url: str) -> str:
        """Extract podcast name from RSS URL."""
        # Implementation would parse RSS feed for podcast title
        # Simplified example
        import feedparser
        feed = feedparser.parse(rss_url)
        return feed.feed.get('title', '')
```

## Error Handling and Fallbacks

```python
from enum import Enum
from typing import Optional

class TranscriptSource(Enum):
    YOUTUBE_MANUAL = "youtube_manual"
    YOUTUBE_AUTO = "youtube_auto"
    WHISPER_LOCAL = "whisper_local"
    WHISPER_REMOTE = "whisper_remote"
    NOT_AVAILABLE = "not_available"

class TranscriptFetcher:
    """Unified transcript fetching with fallback strategy."""
    
    def __init__(self):
        self.youtube_detector = YouTubePodcastDetector()
    
    def get_transcript(
        self,
        podcast_rss: str,
        episode_title: str,
        episode_audio_url: str
    ) -> Tuple[Optional[str], TranscriptSource]:
        """
        Attempt to get transcript using fallback strategy.
        
        Strategy:
        1. Check if available on YouTube with manual transcripts
        2. Check YouTube auto-generated transcripts
        3. Fall back to Whisper transcription
        
        Returns:
            Tuple of (transcript_text, source)
        """
        
        # Step 1: Try YouTube
        is_on_youtube, youtube_url = self.youtube_detector.check_youtube_availability(
            podcast_rss, episode_title
        )
        
        if is_on_youtube and youtube_url:
            # Try manual transcript first
            try:
                transcript = self._get_youtube_manual_transcript(youtube_url)
                if transcript:
                    return (transcript, TranscriptSource.YOUTUBE_MANUAL)
            except:
                pass
            
            # Try auto-generated transcript
            try:
                transcript = self._get_youtube_auto_transcript(youtube_url)
                if transcript:
                    return (transcript, TranscriptSource.YOUTUBE_AUTO)
            except:
                pass
        
        # Step 2: Fall back to Whisper
        try:
            transcript = self._transcribe_with_whisper(episode_audio_url)
            if transcript:
                return (transcript, TranscriptSource.WHISPER_REMOTE)
        except:
            pass
        
        return (None, TranscriptSource.NOT_AVAILABLE)
    
    def _get_youtube_manual_transcript(self, url: str) -> Optional[str]:
        """Get manually created YouTube transcript."""
        video_id = get_youtube_video_id(url)
        if not video_id:
            return None
            
        transcript_list = YouTubeTranscriptApi.list_transcripts(video_id)
        transcript = transcript_list.find_manually_created_transcript(['en'])
        data = transcript.fetch()
        return ' '.join([entry['text'] for entry in data])
    
    def _get_youtube_auto_transcript(self, url: str) -> Optional[str]:
        """Get auto-generated YouTube transcript."""
        video_id = get_youtube_video_id(url)
        if not video_id:
            return None
            
        transcript_list = YouTubeTranscriptApi.list_transcripts(video_id)
        transcript = transcript_list.find_generated_transcript(['en'])
        data = transcript.fetch()
        return ' '.join([entry['text'] for entry in data])
    
    def _transcribe_with_whisper(self, audio_url: str) -> Optional[str]:
        """Transcribe using Whisper (remote or local)."""
        # Implementation would call existing Whisper service
        # This is a placeholder
        from ekko_prototype.pages.tools.audio_transcriber import EpisodeTranscriber
        transcriber = EpisodeTranscriber()
        return transcriber.transcribe(audio_url)
```

## Best Practices

1. **Always try YouTube first** - It's faster and free
2. **Cache transcripts** - Store fetched transcripts to avoid repeated API calls
3. **Handle rate limits** - YouTube API has quotas, implement exponential backoff
4. **Validate transcripts** - Check for quality and completeness
5. **Provide source attribution** - Note whether transcript is manual or auto-generated

## Environment Variables

```bash
# .env file
YOUTUBE_API_KEY=your_api_key_here  # Optional, for search functionality
TRANSCRIPT_CACHE_DIR=./transcript_cache
YOUTUBE_SEARCH_ENABLED=true
```

## Testing

```python
# Test YouTube transcript extraction
def test_youtube_transcript():
    url = "https://www.youtube.com/watch?v=dQw4w9WgXcQ"
    transcript = fetch_youtube_transcript(url)
    assert transcript is not None
    assert len(transcript) > 0
    print(f"Transcript length: {len(transcript)} characters")

# Test fallback mechanism
def test_transcript_fallback():
    fetcher = TranscriptFetcher()
    transcript, source = fetcher.get_transcript(
        podcast_rss="https://example.com/feed.xml",
        episode_title="Episode 123",
        episode_audio_url="https://example.com/episode.mp3"
    )
    print(f"Transcript source: {source.value}")
```