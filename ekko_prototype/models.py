"""
Pydantic models for ekko application.

This module contains all the data models used throughout the ekko application,
providing strong typing and validation for data structures.
"""

from datetime import datetime
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field, HttpUrl, field_validator


class TranscriptSource(str, Enum):
    """
    Enumeration of possible transcript sources.
    
    :cvar YOUTUBE_MANUAL: Manually created YouTube transcript
    :cvar YOUTUBE_AUTO: Auto-generated YouTube transcript
    :cvar WHISPER_LOCAL: Local Whisper model transcription
    :cvar WHISPER_OPENAI: OpenAI Whisper API transcription
    :cvar WHISPER_REMOTE: Remote Whisper server transcription
    :cvar NOT_AVAILABLE: No transcript available
    """
    YOUTUBE_MANUAL = "youtube_manual"
    YOUTUBE_AUTO = "youtube_auto"
    WHISPER_LOCAL = "whisper_local"
    WHISPER_OPENAI = "whisper_openai"
    WHISPER_REMOTE = "whisper_remote"
    NOT_AVAILABLE = "not_available"


class PodcastModel(BaseModel):
    """
    Model for podcast information.
    
    :ivar id: Unique podcast identifier
    :vartype id: int
    :ivar title: Podcast title
    :vartype title: str
    :ivar url: Podcast website URL
    :vartype url: HttpUrl
    :ivar description: Podcast description
    :vartype description: Optional[str]
    :ivar author: Podcast author/creator
    :vartype author: Optional[str]
    :ivar image: Podcast cover image URL
    :vartype image: Optional[HttpUrl]
    :ivar categories: List of podcast categories
    :vartype categories: List[str]
    :ivar language: Primary language code
    :vartype language: Optional[str]
    :ivar explicit: Whether podcast contains explicit content
    :vartype explicit: bool
    """
    id: int = Field(..., description="Unique podcast ID")
    title: str = Field(..., description="Podcast title")
    url: HttpUrl = Field(..., description="Podcast website URL")
    description: str | None = Field(None, description="Podcast description")
    author: str | None = Field(None, description="Podcast author/creator")
    image: HttpUrl | None = Field(None, description="Podcast cover image URL")
    categories: list[str] = Field(default_factory=list, description="Podcast categories")
    language: str | None = Field(None, description="Primary language")
    explicit: bool = Field(False, description="Explicit content flag")
    
    model_config = {
        "json_schema_extra": {
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
    }


class EpisodeModel(BaseModel):
    """
    Model for podcast episode.
    
    :ivar guid: Unique episode identifier
    :vartype guid: str
    :ivar title: Episode title
    :vartype title: str
    :ivar description: Episode description
    :vartype description: Optional[str]
    :ivar published_date: Publication date
    :vartype published_date: Optional[datetime]
    :ivar duration: Episode duration in HH:MM:SS format
    :vartype duration: Optional[str]
    :ivar audio_url: URL to audio file
    :vartype audio_url: Optional[HttpUrl]
    :ivar transcript_url: URL to transcript if available
    :vartype transcript_url: Optional[HttpUrl]
    :ivar image: Episode image URL
    :vartype image: Optional[HttpUrl]
    :ivar season: Season number
    :vartype season: Optional[int]
    :ivar episode_number: Episode number
    :vartype episode_number: Optional[int]
    """
    guid: str = Field(..., description="Unique episode identifier")
    title: str = Field(..., description="Episode title")
    description: str | None = Field(None, description="Episode description")
    published_date: datetime | None = Field(None, description="Publication date")
    duration: str | None = Field(None, description="Episode duration")
    audio_url: HttpUrl | None = Field(None, description="Audio file URL")
    transcript_url: HttpUrl | None = Field(None, description="Transcript URL if available")
    image: HttpUrl | None = Field(None, description="Episode image URL")
    season: int | None = Field(None, description="Season number")
    episode_number: int | None = Field(None, description="Episode number")
    
    @field_validator('duration')
    def validate_duration(self, v):
        """
        Validate and normalize duration format to HH:MM:SS.
        
        :param v: Duration value to validate
        :type v: Any
        
        :return: Normalized duration string in HH:MM:SS format
        :rtype: str
        """
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
    """
    Model for transcript fetch results.
    
    :ivar text: The transcript text
    :vartype text: Optional[str]
    :ivar source: Source of the transcript
    :vartype source: TranscriptSource
    :ivar quality_score: Quality score between 0 and 1
    :vartype quality_score: float
    :ivar language: Detected language code
    :vartype language: Optional[str]
    :ivar duration_seconds: Audio duration in seconds
    :vartype duration_seconds: Optional[int]
    :ivar word_count: Number of words in transcript
    :vartype word_count: Optional[int]
    :ivar metadata: Additional metadata
    :vartype metadata: Dict[str, Any]
    """
    text: str | None = Field(None, description="Transcript text")
    source: TranscriptSource = Field(..., description="Source of transcript")
    quality_score: float = Field(0.0, ge=0.0, le=1.0, description="Quality score (0-1)")
    language: str | None = Field(None, description="Detected language")
    duration_seconds: int | None = Field(None, description="Audio duration in seconds")
    word_count: int | None = Field(None, description="Number of words in transcript")
    metadata: dict[str, Any] = Field(default_factory=dict, description="Additional metadata")
    
    @field_validator('word_count', mode='after')
    def calculate_word_count(self, v, values):
        """
        Calculate word count from text if not provided.
        
        :param v: Current word count value
        :type v: Optional[int]
        :param values: Other field values
        :type values: dict
        
        :return: Word count
        :rtype: Optional[int]
        """
        if v is None and 'text' in values and values['text']:
            return len(values['text'].split())
        return v


class SummaryRequest(BaseModel):
    """
    Model for summary request parameters.
    
    :ivar transcript_text: Text to summarize
    :vartype transcript_text: str
    :ivar summary_type: Type of summary to generate
    :vartype summary_type: str
    :ivar max_length: Maximum summary length
    :vartype max_length: Optional[int]
    :ivar include_timestamps: Whether to include timestamps
    :vartype include_timestamps: bool
    :ivar custom_prompt: Custom prompt for summary
    :vartype custom_prompt: Optional[str]
    """
    transcript_text: str = Field(..., description="Transcript text to summarize")
    summary_type: str = Field("comprehensive", description="Type of summary")
    max_length: int | None = Field(None, description="Maximum summary length")
    include_timestamps: bool = Field(False, description="Include timestamps in summary")
    custom_prompt: str | None = Field(None, description="Custom prompt for summary")


class SummaryResult(BaseModel):
    """Model for summary result."""
    summary: str = Field(..., description="Generated summary")
    key_points: list[str] = Field(default_factory=list, description="Key points extracted")
    topics: list[str] = Field(default_factory=list, description="Main topics discussed")
    action_items: list[str] = Field(default_factory=list, description="Action items identified")
    quotes: list[str] = Field(default_factory=list, description="Notable quotes")
    metadata: dict[str, Any] = Field(default_factory=dict, description="Additional metadata")


class ChatMessage(BaseModel):
    """
    Model for a single chat message.
    
    :ivar role: Message role (user/assistant/system)
    :vartype role: str
    :ivar content: Message content
    :vartype content: str
    :ivar timestamp: When message was created
    :vartype timestamp: datetime
    :ivar metadata: Additional message metadata
    :vartype metadata: Dict[str, Any]
    """
    role: str = Field(..., pattern="^(user|assistant|system)$", description="Message role")
    content: str = Field(..., description="Message content")
    timestamp: datetime = Field(default_factory=datetime.now, description="Message timestamp")
    metadata: dict[str, Any] = Field(default_factory=dict, description="Additional metadata")


class ChatSession(BaseModel):
    """Model for chat session."""
    session_id: str = Field(..., description="Unique session identifier")
    podcast_id: int | None = Field(None, description="Associated podcast ID")
    episode_guid: str | None = Field(None, description="Associated episode GUID")
    messages: list[ChatMessage] = Field(default_factory=list, description="Chat messages")
    created_at: datetime = Field(default_factory=datetime.now, description="Session creation time")
    updated_at: datetime = Field(default_factory=datetime.now, description="Last update time")
    
    def add_message(self, role: str, content: str) -> None:
        """
        Add a message to the chat session.
        
        :param role: Role of the message sender (user/assistant/system)
        :type role: str
        :param content: Content of the message
        :type content: str
        
        .. note::
           Automatically updates the session's updated_at timestamp.
        """
        message = ChatMessage(role=role, content=content)
        self.messages.append(message)
        self.updated_at = datetime.now()


class FeedbackModel(BaseModel):
    """Model for user feedback."""
    user_id: str | None = Field(None, description="User identifier")
    session_id: str = Field(..., description="Session identifier")
    feedback_type: str = Field(..., description="Type of feedback")
    rating: int | None = Field(None, ge=1, le=5, description="Rating (1-5)")
    comment: str | None = Field(None, description="User comment")
    metadata: dict[str, Any] = Field(default_factory=dict, description="Additional metadata")
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
    languages: list[str] = Field(default_factory=lambda: ["en"], description="Preferred languages")


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
    
    model_config = {
        "env_prefix": "EKKO_"
    }