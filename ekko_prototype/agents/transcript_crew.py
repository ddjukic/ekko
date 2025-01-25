"""
CrewAI-powered transcript fetching agents for ekko.

This module implements intelligent agents that work together to fetch
transcripts from various sources with quality validation.
"""

import logging
import os
from typing import Any

from crewai import Agent, Crew, Process, Task
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI

from ..pages.tools.transcript_fetcher import TranscriptConfig, UnifiedTranscriptFetcher
from ..pages.tools.youtube_detector import TranscriptSource, YouTubePodcastDetector

load_dotenv()
logger = logging.getLogger(__name__)


class TranscriptCrew:
    """
    CrewAI implementation for intelligent transcript fetching.
    
    This class coordinates multiple specialized agents to find and
    extract transcripts from various sources.
    """
    
    def __init__(self, openai_api_key: str | None = None):
        """
        Initialize the transcript crew with specialized agents.
        
        Args:
            openai_api_key: OpenAI API key (defaults to env variable)
        """
        self.api_key = openai_api_key or os.getenv("OPENAI_API_KEY")
        if not self.api_key:
            raise ValueError("OpenAI API key is required")
        
        self.llm = ChatOpenAI(
            model="gpt-4",
            temperature=0.3,
            api_key=self.api_key
        )
        
        # Initialize tools
        self.youtube_detector = YouTubePodcastDetector()
        self.transcript_fetcher = UnifiedTranscriptFetcher(
            TranscriptConfig(
                prefer_youtube=True,
                cache_transcripts=True
            )
        )
        
        self._setup_agents()
    
    def _setup_agents(self):
        """Initialize specialized agents for transcript operations."""
        
        # YouTube Search Agent
        self.youtube_searcher = Agent(
            role='YouTube Podcast Specialist',
            goal='Find podcast episodes on YouTube and verify their availability',
            backstory="""You are an expert at finding podcast episodes on YouTube.
            You understand different naming conventions, can identify official uploads,
            and know how to search effectively for episodes across various channels.
            You're meticulous about verifying that the found video matches the requested episode.""",
            verbose=True,
            allow_delegation=False,
            llm=self.llm,
            max_iter=3
        )
        
        # Transcript Extractor Agent
        self.transcript_extractor = Agent(
            role='Transcript Extraction Expert',
            goal='Extract high-quality transcripts from available sources',
            backstory="""You specialize in extracting transcripts from various sources.
            You prioritize accuracy and completeness, always preferring manually-created
            transcripts over auto-generated ones. You know how to handle different
            transcript formats and can identify quality issues.""",
            verbose=True,
            allow_delegation=False,
            llm=self.llm,
            max_iter=5
        )
        
        # Audio Transcription Agent
        self.audio_transcriber = Agent(
            role='Audio Transcription Specialist',
            goal='Transcribe audio when transcripts are unavailable',
            backstory="""You are an expert in audio transcription using Whisper AI.
            You handle the fallback scenario when YouTube transcripts are not available.
            You understand audio quality requirements, can optimize for different
            Whisper models, and ensure accurate transcription even for challenging audio.""",
            verbose=True,
            allow_delegation=False,
            llm=self.llm,
            max_iter=3
        )
        
        # Quality Validator Agent
        self.quality_validator = Agent(
            role='Transcript Quality Assurance Specialist',
            goal='Validate and improve transcript quality',
            backstory="""You ensure transcripts meet the highest quality standards.
            You check for completeness, accuracy, proper formatting, and readability.
            You can identify common transcription errors, fix formatting issues,
            and enhance the overall quality of transcripts for better comprehension.""",
            verbose=True,
            allow_delegation=False,
            llm=self.llm,
            max_iter=2
        )
    
    def fetch_transcript(
        self,
        podcast_name: str,
        episode_title: str,
        episode_audio_url: str | None = None,
        podcast_rss_url: str | None = None
    ) -> dict[str, Any]:
        """
        Orchestrate agents to fetch transcript using the best available method.
        
        Args:
            podcast_name: Name of the podcast
            episode_title: Title of the episode
            episode_audio_url: URL of the audio file (fallback)
            podcast_rss_url: RSS feed URL of the podcast
            
        Returns:
            Dictionary containing transcript and metadata
        """
        
        # Task 1: Search for episode on YouTube
        search_task = Task(
            description=f"""
            Search for the following podcast episode on YouTube:
            - Podcast: {podcast_name}
            - Episode: {episode_title}
            
            Your objectives:
            1. Search for the episode using various search strategies
            2. Identify if there's an official upload from the podcast channel
            3. Verify the found video matches the requested episode
            4. Return the YouTube URL if found, or 'not found' if unavailable
            
            Consider variations in naming, episode numbers, and guest names.
            """,
            expected_output="YouTube URL of the episode or 'not found'",
            agent=self.youtube_searcher
        )
        
        # Task 2: Extract transcript from YouTube
        extract_task = Task(
            description="""
            If a YouTube URL was found in the previous task, extract the transcript.
            
            Your objectives:
            1. Attempt to get manually-created transcripts first
            2. Fall back to auto-generated transcripts if manual ones aren't available
            3. Verify the transcript is complete and not truncated
            4. Format the transcript for readability
            5. Return the full transcript text or 'not available' if extraction fails
            
            Quality check: Ensure the transcript has reasonable length (>500 words for a typical episode).
            """,
            expected_output="Complete transcript text or 'not available'",
            agent=self.transcript_extractor
        )
        
        # Task 3: Fallback to audio transcription
        transcribe_task = Task(
            description=f"""
            If YouTube transcript is not available, transcribe the audio from: {episode_audio_url}
            
            Your objectives:
            1. Download the audio file efficiently
            2. Use Whisper AI for transcription
            3. Choose appropriate model based on audio length
            4. Ensure complete transcription without truncation
            5. Return the transcribed text
            
            Use remote Whisper service if available, otherwise use local Whisper.
            """,
            expected_output="Transcribed text from audio",
            agent=self.audio_transcriber
        )
        
        # Task 4: Validate and enhance quality
        validate_task = Task(
            description="""
            Validate and enhance the transcript quality from previous tasks.
            
            Your objectives:
            1. Check for completeness (no truncation or missing sections)
            2. Verify proper sentence structure and punctuation
            3. Identify and fix common transcription errors
            4. Add paragraph breaks for better readability
            5. Check for speaker identification if available
            6. Ensure timestamps are properly formatted if present
            
            Quality metrics to verify:
            - Minimum word count appropriate for episode length
            - Proper capitalization and punctuation
            - No excessive repetition or artifacts
            - Clear paragraph organization
            
            Return the validated and cleaned transcript.
            """,
            expected_output="Validated and enhanced transcript with quality report",
            agent=self.quality_validator
        )
        
        # Create crew with sequential process
        crew = Crew(
            agents=[
                self.youtube_searcher,
                self.transcript_extractor,
                self.audio_transcriber,
                self.quality_validator
            ],
            tasks=[search_task, extract_task, transcribe_task, validate_task],
            process=Process.sequential,
            verbose=True,
            memory=True,
            cache=True,
            max_rpm=10
        )
        
        # Execute crew
        logger.info(f"Starting transcript fetch for: {podcast_name} - {episode_title}")
        result = crew.kickoff()
        
        # Process result
        return self._process_crew_result(result, podcast_name, episode_title)
    
    def _process_crew_result(
        self,
        result: str,
        podcast_name: str,
        episode_title: str
    ) -> dict[str, Any]:
        """
        Process the crew execution result into structured output.
        
        Args:
            result: Raw result from crew execution
            podcast_name: Name of the podcast
            episode_title: Title of the episode
            
        Returns:
            Structured dictionary with transcript and metadata
        """
        # Determine source based on result content
        source = TranscriptSource.NOT_AVAILABLE
        if "YouTube" in str(result):
            if "manual" in str(result).lower():
                source = TranscriptSource.YOUTUBE_MANUAL
            else:
                source = TranscriptSource.YOUTUBE_AUTO
        elif "Whisper" in str(result):
            if "remote" in str(result).lower():
                source = TranscriptSource.WHISPER_REMOTE
            else:
                source = TranscriptSource.WHISPER_LOCAL
        
        # Calculate quality score
        quality_score = self._calculate_quality_score(str(result))
        
        return {
            'transcript': str(result),
            'source': source.value,
            'quality_score': quality_score,
            'podcast_name': podcast_name,
            'episode_title': episode_title,
            'metadata': {
                'processing_method': 'CrewAI',
                'agents_used': 4,
                'word_count': len(str(result).split()) if result else 0
            }
        }
    
    def _calculate_quality_score(self, transcript: str) -> float:
        """
        Calculate quality score for the transcript.
        
        Args:
            transcript: Transcript text
            
        Returns:
            Quality score between 0.0 and 1.0
        """
        if not transcript:
            return 0.0
        
        score = 1.0
        word_count = len(transcript.split())
        
        # Penalize short transcripts
        if word_count < 500:
            score -= 0.3
        elif word_count < 1000:
            score -= 0.1
        
        # Check for quality indicators
        if "[inaudible]" in transcript.lower():
            score -= 0.1
        if "[music]" in transcript.lower():
            score -= 0.05
        if transcript.count("...") > 20:
            score -= 0.05
        
        # Check for proper structure
        if transcript.count('.') < 10:
            score -= 0.1
        if transcript.count('\n\n') < 3:  # Few paragraph breaks
            score -= 0.05
        
        return max(0.0, min(1.0, score))


class TranscriptOrchestrator:
    """
    Main orchestrator for transcript operations using CrewAI.
    
    This class provides a high-level interface for transcript fetching
    and coordinates with other system components.
    """
    
    def __init__(self, openai_api_key: str | None = None):
        """
        Initialize the transcript orchestrator.
        
        Args:
            openai_api_key: OpenAI API key (defaults to env variable)
        """
        self.transcript_crew = TranscriptCrew(openai_api_key)
        
        # Also initialize the fallback fetcher for direct operations
        self.fallback_fetcher = UnifiedTranscriptFetcher(
            TranscriptConfig(
                prefer_youtube=True,
                cache_transcripts=True
            )
        )
    
    def get_transcript(
        self,
        podcast_name: str,
        episode_title: str,
        episode_audio_url: str | None = None,
        podcast_rss_url: str | None = None,
        use_crew: bool = True
    ) -> dict[str, Any]:
        """
        Get transcript using CrewAI or fallback to direct fetching.
        
        Args:
            podcast_name: Name of the podcast
            episode_title: Title of the episode
            episode_audio_url: URL of the audio file
            podcast_rss_url: RSS feed URL
            use_crew: Whether to use CrewAI agents
            
        Returns:
            Dictionary with transcript and metadata
        """
        try:
            if use_crew:
                logger.info("Using CrewAI agents for transcript fetching")
                return self.transcript_crew.fetch_transcript(
                    podcast_name=podcast_name,
                    episode_title=episode_title,
                    episode_audio_url=episode_audio_url,
                    podcast_rss_url=podcast_rss_url
                )
            else:
                logger.info("Using direct transcript fetching")
                result = self.fallback_fetcher.get_transcript(
                    podcast_name=podcast_name,
                    episode_title=episode_title,
                    episode_audio_url=episode_audio_url,
                    podcast_rss_url=podcast_rss_url
                )
                
                return {
                    'transcript': result.text,
                    'source': result.source.value,
                    'quality_score': result.quality_score,
                    'podcast_name': podcast_name,
                    'episode_title': episode_title,
                    'metadata': result.metadata
                }
                
        except Exception as e:
            logger.error(f"Error fetching transcript: {e}")
            return {
                'transcript': None,
                'source': TranscriptSource.NOT_AVAILABLE.value,
                'quality_score': 0.0,
                'podcast_name': podcast_name,
                'episode_title': episode_title,
                'metadata': {'error': str(e)}
            }