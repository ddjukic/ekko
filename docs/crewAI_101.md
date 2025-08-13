# CrewAI Framework Guide for ekko

## Overview

CrewAI is a Python framework for orchestrating role-playing, autonomous AI agents. It enables collaborative intelligence where agents work together seamlessly to tackle complex tasks.

## Installation

```bash
# CrewAI requires Python 3.10-3.13
uv add crewai
uv add crewai-tools  # Optional: for additional tools
```

## Core Concepts

### 1. Agents
Agents are autonomous units with specific roles, goals, and backstories.

```python
from crewai import Agent
from langchain_openai import ChatOpenAI

# Initialize LLM (can use different models)
llm = ChatOpenAI(model="gpt-4", temperature=0.7)

# Create an agent
researcher = Agent(
    role='Senior Research Analyst',
    goal='Discover and analyze cutting-edge developments in AI',
    backstory="""You are a seasoned researcher with a keen eye for detail.
    You excel at finding relevant information and presenting it clearly.""",
    verbose=True,
    allow_delegation=False,
    llm=llm,
    tools=[],  # Add tools here
    max_iter=3,  # Maximum iterations for task completion
    memory=True  # Enable memory for context retention
)
```

### 2. Tasks
Tasks are specific assignments for agents to complete.

```python
from crewai import Task

research_task = Task(
    description="""Conduct comprehensive research on the latest AI trends.
    Focus on practical applications and emerging technologies.
    Provide a detailed analysis with sources.""",
    expected_output="A detailed report on AI trends with citations",
    agent=researcher,
    tools=[],  # Task-specific tools
)
```

### 3. Crews
Crews orchestrate multiple agents working together.

```python
from crewai import Crew, Process

crew = Crew(
    agents=[researcher, writer, reviewer],
    tasks=[research_task, writing_task, review_task],
    process=Process.sequential,  # or Process.hierarchical
    verbose=True,
    memory=True,  # Enable crew-level memory
    cache=True,  # Cache results for efficiency
    max_rpm=10,  # Rate limiting for API calls
)

# Execute the crew
result = crew.kickoff()
print(result)
```

## ekko-Specific Implementation

### Podcast Transcript Agent System

```python
from crewai import Agent, Task, Crew
from typing import Optional, Dict, Any
import os
from dotenv import load_dotenv

load_dotenv()

class PodcastTranscriptCrew:
    """CrewAI implementation for intelligent transcript fetching."""

    def __init__(self):
        self.llm = ChatOpenAI(
            model="gpt-4",
            temperature=0.3,
            api_key=os.getenv("OPENAI_API_KEY")
        )
        self._setup_agents()
        self._setup_tools()

    def _setup_agents(self):
        """Initialize specialized agents."""

        # YouTube Search Agent
        self.youtube_searcher = Agent(
            role='YouTube Podcast Finder',
            goal='Find podcast episodes on YouTube and verify availability',
            backstory="""You are an expert at finding podcast episodes on YouTube.
            You know how to search effectively and identify the correct videos.""",
            verbose=True,
            allow_delegation=False,
            llm=self.llm,
            tools=[],  # Add YouTube search tools
            max_iter=3
        )

        # Transcript Extractor Agent
        self.transcript_extractor = Agent(
            role='Transcript Extraction Specialist',
            goal='Extract high-quality transcripts from various sources',
            backstory="""You specialize in extracting transcripts from YouTube videos.
            You prioritize manual transcripts over auto-generated ones.""",
            verbose=True,
            allow_delegation=False,
            llm=self.llm,
            tools=[],  # Add transcript extraction tools
            max_iter=5
        )

        # Audio Transcription Agent
        self.audio_transcriber = Agent(
            role='Audio Transcription Expert',
            goal='Transcribe audio using Whisper when transcripts are unavailable',
            backstory="""You are an expert in audio transcription using Whisper.
            You handle the fallback when YouTube transcripts are not available.""",
            verbose=True,
            allow_delegation=False,
            llm=self.llm,
            tools=[],  # Add Whisper transcription tools
            max_iter=3
        )

        # Quality Validator Agent
        self.quality_validator = Agent(
            role='Transcript Quality Assurance',
            goal='Validate and improve transcript quality',
            backstory="""You ensure transcripts meet quality standards.
            You check for completeness, accuracy, and readability.""",
            verbose=True,
            allow_delegation=False,
            llm=self.llm,
            max_iter=2
        )

    def _setup_tools(self):
        """Set up tools for agents."""
        from crewai_tools import SerperDevTool, WebsiteSearchTool

        # Search tool for YouTube
        self.search_tool = SerperDevTool(
            api_key=os.getenv("SERPER_API_KEY")
        )

        # Custom tools can be added here
        self.youtube_searcher.tools = [self.search_tool]

    def fetch_transcript(
        self,
        podcast_name: str,
        episode_title: str,
        audio_url: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Orchestrate agents to fetch transcript.

        Args:
            podcast_name: Name of the podcast
            episode_title: Title of the episode
            audio_url: Fallback audio URL if YouTube not available

        Returns:
            Dict with transcript and metadata
        """

        # Task 1: Search for episode on YouTube
        search_task = Task(
            description=f"""Search for the podcast episode on YouTube:
            Podcast: {podcast_name}
            Episode: {episode_title}

            Find the official upload if available.
            Return the YouTube URL if found.""",
            expected_output="YouTube URL or 'not found'",
            agent=self.youtube_searcher
        )

        # Task 2: Extract transcript from YouTube
        extract_task = Task(
            description="""If YouTube URL is found, extract the transcript.
            Prioritize manual transcripts over auto-generated.
            Return the full transcript text.""",
            expected_output="Transcript text or 'not available'",
            agent=self.transcript_extractor
        )

        # Task 3: Fallback to audio transcription
        transcribe_task = Task(
            description=f"""If YouTube transcript is not available,
            transcribe the audio from: {audio_url}
            Use Whisper for high-quality transcription.""",
            expected_output="Transcribed text",
            agent=self.audio_transcriber
        )

        # Task 4: Validate quality
        validate_task = Task(
            description="""Validate the transcript quality.
            Check for:
            - Completeness
            - Proper formatting
            - Speaker identification (if available)
            - Timestamp markers

            Clean up any issues found.""",
            expected_output="Validated and cleaned transcript",
            agent=self.quality_validator
        )

        # Create crew with conditional workflow
        crew = Crew(
            agents=[
                self.youtube_searcher,
                self.transcript_extractor,
                self.audio_transcriber,
                self.quality_validator
            ],
            tasks=[search_task, extract_task, transcribe_task, validate_task],
            process=Process.sequential,
            verbose=True
        )

        # Execute crew
        result = crew.kickoff()

        return {
            'transcript': result,
            'source': self._determine_source(result),
            'quality_score': self._calculate_quality_score(result)
        }

    def _determine_source(self, result: str) -> str:
        """Determine the source of the transcript."""
        # Logic to determine if from YouTube or Whisper
        if "YouTube" in result:
            return "YouTube"
        return "Whisper"

    def _calculate_quality_score(self, transcript: str) -> float:
        """Calculate quality score of transcript."""
        # Simple quality scoring logic
        score = 1.0
        if len(transcript) < 1000:
            score -= 0.3
        if "[inaudible]" in transcript:
            score -= 0.1
        return max(0.0, score)
```

### Summary Generation Crew

```python
class SummaryCrew:
    """CrewAI implementation for podcast summarization."""

    def __init__(self, summary_style: str = "comprehensive"):
        self.summary_style = summary_style
        self.llm = ChatOpenAI(model="gpt-4", temperature=0.5)
        self._setup_agents()

    def _setup_agents(self):
        """Initialize summary generation agents."""

        # Content Analyzer
        self.analyzer = Agent(
            role='Content Analysis Expert',
            goal='Extract key insights and themes from podcast transcripts',
            backstory="""You excel at identifying the most important ideas,
            insights, and actionable advice from long-form content.""",
            verbose=True,
            llm=self.llm
        )

        # Summary Writer
        self.writer = Agent(
            role='Summary Writing Specialist',
            goal='Create clear, concise, and engaging summaries',
            backstory="""You are a skilled writer who creates summaries that
            capture the essence of content while being easy to read.""",
            verbose=True,
            llm=self.llm
        )

        # Fact Checker
        self.fact_checker = Agent(
            role='Fact Verification Expert',
            goal='Verify claims and ensure accuracy in summaries',
            backstory="""You ensure all facts and claims in summaries are
            accurate and properly attributed.""",
            verbose=True,
            llm=self.llm
        )

    def generate_summary(self, transcript: str) -> Dict[str, Any]:
        """Generate comprehensive podcast summary."""

        # Task 1: Analyze content
        analysis_task = Task(
            description=f"""Analyze this podcast transcript and extract:
            - Main topics discussed
            - Key insights and takeaways
            - Notable quotes
            - Action items or advice

            Transcript: {transcript[:3000]}...""",  # Truncate for prompt
            expected_output="Structured analysis with bullet points",
            agent=self.analyzer
        )

        # Task 2: Write summary
        writing_task = Task(
            description=f"""Based on the analysis, write a {self.summary_style} summary.
            Include:
            - Executive summary (2-3 sentences)
            - Main topics with key points
            - Notable insights
            - Actionable takeaways

            Make it engaging and easy to scan.""",
            expected_output="Well-formatted summary",
            agent=self.writer
        )

        # Task 3: Verify facts
        verification_task = Task(
            description="""Review the summary for accuracy.
            Ensure all claims are supported by the transcript.
            Flag any statements that need clarification.""",
            expected_output="Verified summary with accuracy notes",
            agent=self.fact_checker
        )

        # Create and execute crew
        crew = Crew(
            agents=[self.analyzer, self.writer, self.fact_checker],
            tasks=[analysis_task, writing_task, verification_task],
            process=Process.sequential,
            verbose=True
        )

        result = crew.kickoff()

        return {
            'summary': result,
            'word_count': len(result.split()),
            'reading_time': self._calculate_reading_time(result)
        }

    def _calculate_reading_time(self, text: str) -> int:
        """Calculate reading time in minutes."""
        words_per_minute = 200
        word_count = len(text.split())
        return max(1, word_count // words_per_minute)
```

### Custom Tools for CrewAI

```python
from crewai_tools import BaseTool
from typing import Type
from pydantic import BaseModel, Field

class YouTubeSearchInput(BaseModel):
    """Input schema for YouTube search."""
    query: str = Field(..., description="Search query for YouTube")

class YouTubeSearchTool(BaseTool):
    name: str = "YouTube Search"
    description: str = "Search for videos on YouTube"
    args_schema: Type[BaseModel] = YouTubeSearchInput

    def _run(self, query: str) -> str:
        """Execute YouTube search."""
        # Implementation using youtube-transcript-api or yt-dlp
        from ekko_prototype.tools.youtube_detector import YouTubePodcastDetector
        detector = YouTubePodcastDetector()
        result = detector.search_youtube_for_episode("", query)
        return result or "No results found"

class WhisperTranscriptionInput(BaseModel):
    """Input schema for Whisper transcription."""
    audio_url: str = Field(..., description="URL of audio file")

class WhisperTranscriptionTool(BaseTool):
    name: str = "Whisper Transcription"
    description: str = "Transcribe audio using Whisper"
    args_schema: Type[BaseModel] = WhisperTranscriptionInput

    def _run(self, audio_url: str) -> str:
        """Execute Whisper transcription."""
        from ekko_prototype.pages.tools.audio_transcriber import EpisodeTranscriber
        transcriber = EpisodeTranscriber()
        result = transcriber.transcribe(audio_url)
        return result or "Transcription failed"
```

## Advanced Features

### Memory and Context

```python
# Enable memory for context retention across tasks
crew = Crew(
    agents=[...],
    tasks=[...],
    memory=True,  # Enable crew memory
    embedder={
        "provider": "openai",
        "config": {
            "model": "text-embedding-3-small"
        }
    }
)
```

### Hierarchical Process

```python
# Use hierarchical process for complex workflows
crew = Crew(
    agents=[manager, researcher, writer],
    tasks=[...],
    process=Process.hierarchical,
    manager_llm=ChatOpenAI(model="gpt-4"),  # Manager uses GPT-4
    verbose=True
)
```

### Async Execution

```python
import asyncio

async def run_crew_async():
    """Run crew asynchronously."""
    crew = Crew(agents=[...], tasks=[...])
    result = await crew.kickoff_async()
    return result

# Run async
result = asyncio.run(run_crew_async())
```

## Integration with ekko

### Main Integration Point

```python
# ekko_prototype/agents/transcript_crew.py
from crewai import Crew
from typing import Optional

class TranscriptOrchestrator:
    """Main orchestrator for transcript operations."""

    def __init__(self):
        self.transcript_crew = PodcastTranscriptCrew()
        self.summary_crew = SummaryCrew()

    def process_episode(
        self,
        podcast_name: str,
        episode_title: str,
        audio_url: str
    ) -> Dict[str, Any]:
        """
        Full pipeline: fetch transcript → generate summary.
        """
        # Step 1: Get transcript
        transcript_result = self.transcript_crew.fetch_transcript(
            podcast_name=podcast_name,
            episode_title=episode_title,
            audio_url=audio_url
        )

        # Step 2: Generate summary
        if transcript_result['transcript']:
            summary_result = self.summary_crew.generate_summary(
                transcript=transcript_result['transcript']
            )

            return {
                'transcript': transcript_result['transcript'],
                'transcript_source': transcript_result['source'],
                'summary': summary_result['summary'],
                'reading_time': summary_result['reading_time'],
                'quality_score': transcript_result['quality_score']
            }

        return {'error': 'Could not fetch transcript'}
```

## Environment Variables

```bash
# .env configuration for CrewAI
OPENAI_API_KEY=your_openai_key
SERPER_API_KEY=your_serper_key  # For web search
LANGCHAIN_TRACING_V2=true  # Optional: for debugging
LANGCHAIN_API_KEY=your_langsmith_key  # Optional: for tracing
```

## Best Practices

1. **Agent Design**
   - Keep roles focused and specific
   - Write clear, detailed backstories
   - Limit agent capabilities to their expertise

2. **Task Definition**
   - Be explicit about expected outputs
   - Break complex tasks into smaller steps
   - Provide context and examples

3. **Crew Composition**
   - Use 3-5 agents for optimal performance
   - Choose process type based on task complexity
   - Enable memory for context-heavy operations

4. **Performance**
   - Cache results when possible
   - Use rate limiting to avoid API throttling
   - Monitor token usage and costs

5. **Error Handling**
   - Implement fallback mechanisms
   - Log agent interactions for debugging
   - Validate outputs at each step

## Testing

```python
def test_transcript_crew():
    """Test transcript fetching crew."""
    crew = PodcastTranscriptCrew()
    result = crew.fetch_transcript(
        podcast_name="Test Podcast",
        episode_title="Episode 1",
        audio_url="https://example.com/audio.mp3"
    )

    assert 'transcript' in result
    assert 'source' in result
    print(f"Source: {result['source']}")
    print(f"Quality: {result['quality_score']}")

def test_summary_generation():
    """Test summary generation crew."""
    crew = SummaryCrew(summary_style="concise")

    sample_transcript = "This is a test transcript..."
    result = crew.generate_summary(sample_transcript)

    assert 'summary' in result
    assert result['word_count'] > 0
    print(f"Summary: {result['summary'][:200]}...")
```
