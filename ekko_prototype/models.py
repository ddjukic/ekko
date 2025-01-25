"""
Pydantic models for ekko application.

This module contains all the data models used throughout the ekko application,
providing strong typing and validation for data structures.
"""

from datetime import datetime
from enum import Enum
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field, HttpUrl, validator, EmailStr


class TranscriptSource(str, Enum):
    """Source of transcript."""
    YOUTUBE_MANUAL = "youtube_manual"
    YOUTUBE_AUTO = "youtube_auto"
    WHISPER_LOCAL = "whisper_local"
    WHISPER_OPENAI = "whisper_openai"
    WHISPER_REMOTE = "whisper_remote"
    NOT_AVAILABLE = "not_available"


class PodcastModel(BaseModel):
    """Model for podcast information."""
    id: int = Field(..., description="Unique podcast ID")
    title: str = Field(..., description="Podcast title")
    url: HttpUrl = Field(..., description="Podcast website URL")
    description: Optional[str] = Field(None, description="Podcast description")
    author: Optional[str] = Field(None, description="Podcast author/creator")
    image: Optional[HttpUrl] = Field(None, description="Podcast cover image URL")
    categories: List[str] = Field(default_factory=list, description="Podcast categories")
    language: Optional[str] = Field(None, description="Primary language")
    explicit: bool = Field(False, description="Explicit content flag")
    
    class Config:
        schema_extra = {
            "example": {
                "id": 1234,
                "title": "Lenny's Podcast",
                "url": "https://lennyrachitsky.com",
                "description": "Product | Growth | Career",
                "author": "Lenny Rachitsky",
                "image": "https://example.com/image.jpg",
                "categories": ["Technology", "Business"],
                "language": "en",
                "explicit": False
            }
        }


class EpisodeModel(BaseModel):
    """Model for podcast episode."""
    guid: str = Field(..., description="Unique episode identifier")
    title: str = Field(..., description="Episode title")
    description: Optional[str] = Field(None, description="Episode description")
    published_date: Optional[datetime] = Field(None, description="Publication date")
    duration: Optional[str] = Field(None, description="Episode duration")
    audio_url: Optional[HttpUrl] = Field(None, description="Audio file URL")
    transcript_url: Optional[HttpUrl] = Field(None, description="Transcript URL if available")
    image: Optional[HttpUrl] = Field(None, description="Episode image URL")
    season: Optional[int] = Field(None, description="Season number")
    episode_number: Optional[int] = Field(None, description="Episode number")
    
    @validator('duration')
    def validate_duration(cls, v):
        """Validate duration format."""
        if v and ':' not in v:
            # Convert seconds to HH:MM:SS format
            try:
                seconds = int(v)
                hours = seconds // 3600
                minutes = (seconds % 3600) // 60
                secs = seconds % 60
                return f"{hours:02d}:{minutes:02d}:{secs:02d}"
            except ValueError:
                pass
        return v


class TranscriptResult(BaseModel):
    """Model for transcript result."""
    text: Optional[str] = Field(None, description="Transcript text")
    source: TranscriptSource = Field(..., description="Source of transcript")
    quality_score: float = Field(0.0, ge=0.0, le=1.0, description="Quality score (0-1)")
    language: Optional[str] = Field(None, description="Detected language")
    duration_seconds: Optional[int] = Field(None, description="Audio duration in seconds")
    word_count: Optional[int] = Field(None, description="Number of words in transcript")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")
    
    @validator('word_count', always=True)
    def calculate_word_count(cls, v, values):
        """Calculate word count from text if not provided."""
        if v is None and 'text' in values and values['text']:
            return len(values['text'].split())
        return v


class SummaryRequest(BaseModel):
    """Model for summary request."""
    transcript_text: str = Field(..., description="Transcript text to summarize")
    summary_type: str = Field("comprehensive", description="Type of summary")
    max_length: Optional[int] = Field(None, description="Maximum summary length")
    include_timestamps: bool = Field(False, description="Include timestamps in summary")
    custom_prompt: Optional[str] = Field(None, description="Custom prompt for summary")


class SummaryResult(BaseModel):
    """Model for summary result."""
    summary: str = Field(..., description="Generated summary")
    key_points: List[str] = Field(default_factory=list, description="Key points extracted")
    topics: List[str] = Field(default_factory=list, description="Main topics discussed")
    action_items: List[str] = Field(default_factory=list, description="Action items identified")
    quotes: List[str] = Field(default_factory=list, description="Notable quotes")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")


class ChatMessage(BaseModel):
    """Model for chat message."""
    role: str = Field(..., pattern="^(user|assistant|system)$", description="Message role")
    content: str = Field(..., description="Message content")
    timestamp: datetime = Field(default_factory=datetime.now, description="Message timestamp")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")


class ChatSession(BaseModel):
    """Model for chat session."""
    session_id: str = Field(..., description="Unique session identifier")
    podcast_id: Optional[int] = Field(None, description="Associated podcast ID")
    episode_guid: Optional[str] = Field(None, description="Associated episode GUID")
    messages: List[ChatMessage] = Field(default_factory=list, description="Chat messages")
    created_at: datetime = Field(default_factory=datetime.now, description="Session creation time")
    updated_at: datetime = Field(default_factory=datetime.now, description="Last update time")
    
    def add_message(self, role: str, content: str) -> None:
        """Add a message to the session."""
        message = ChatMessage(role=role, content=content)
        self.messages.append(message)
        self.updated_at = datetime.now()


class FeedbackModel(BaseModel):
    """Model for user feedback."""
    user_id: Optional[str] = Field(None, description="User identifier")
    session_id: str = Field(..., description="Session identifier")
    feedback_type: str = Field(..., description="Type of feedback")
    rating: Optional[int] = Field(None, ge=1, le=5, description="Rating (1-5)")
    comment: Optional[str] = Field(None, description="User comment")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")
    created_at: datetime = Field(default_factory=datetime.now, description="Feedback timestamp")


class TranscriptConfig(BaseModel):
    """Configuration for transcript fetching."""
    prefer_youtube: bool = Field(True, description="Prefer YouTube transcripts")
    use_openai_whisper: bool = Field(True, description="Use OpenAI Whisper API")
    use_remote_whisper: bool = Field(False, description="Use remote Whisper server")
    cache_transcripts: bool = Field(True, description="Cache transcripts locally")
    cache_dir: str = Field("./transcript_cache", description="Cache directory")
    max_cache_size_mb: int = Field(500, description="Maximum cache size in MB")
    whisper_model: str = Field("whisper-1", description="Whisper model to use")
    languages: List[str] = Field(default_factory=lambda: ["en"], description="Preferred languages")


class AppSettings(BaseModel):
    """Application settings model."""
    app_name: str = Field("ekko", description="Application name")
    version: str = Field("0.2.0", description="Application version")
    debug: bool = Field(False, description="Debug mode")
    log_level: str = Field("INFO", description="Logging level")
    max_episodes_display: int = Field(20, description="Maximum episodes to display")
    summary_model: str = Field("gpt-4o", description="Model for summarization")
    chat_model: str = Field("gpt-4o", description="Model for chat")
    rate_limit_enabled: bool = Field(False, description="Enable rate limiting")
    demo_user_limit: int = Field(2, description="Podcast limit for demo users")
    
    class Config:
        env_prefix = "EKKO_"