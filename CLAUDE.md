# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview
Ekko is a podcast discovery, curation, and summarization tool built with Streamlit and Python. It provides AI-powered podcast transcription and summarization capabilities, helping users consume content more efficiently.

## Architecture
The project consists of several key components:

1. **Main Streamlit Application** (`ekko_prototype/`)
   - Entry point: `landing.py` - Welcome page and onboarding
   - Main app: `pages/app.py` - Core podcast search, transcription, and summarization interface
   - Feedback system: `pages/feedback_record.py` - User feedback collection

2. **Transcription Service** (`ekko_prototype/pages/tools/transcriber_server.py`)
   - FastAPI server with ngrok tunneling for remote transcription
   - Uses Whisper model for audio-to-text conversion
   - Authentication via bearer token (currently hardcoded as `chamberOfSecrets`)

3. **Core Tools** (`ekko_prototype/pages/tools/`)
   - `podcast_finder.py` - Podcast discovery via PodcastIndex API
   - `feed_parser.py` - RSS feed parsing
   - `summary_creator.py` - OpenAI GPT-4 powered summarization
   - `podcast_chatbot.py` - Chat interface for podcast content
   - `audio_transcriber.py` - Local Whisper transcription
   - `episode_downloader.py` - Podcast episode downloading

4. **RSS Parser Module** (`rss_parser/`)
   - Standalone RSS feed parsing and episode downloading
   - SQLite database for tracking downloads

## Development Commands

### Running the Application
```bash
# Main Streamlit app
streamlit run ekko_prototype/landing.py

# Transcription server (separate terminal)
cd ekko_prototype/pages/tools
python transcriber_server.py
```

### Dependencies
```bash
# Install all dependencies
pip install -r requirements.txt

# Key dependencies include:
# - streamlit, streamlit-feedback, streamlit-pills
# - openai, langchain, chromadb (for AI/chat features)
# - torch, transformers (for local Whisper model)
# - feedparser, requests (for RSS/podcast fetching)
```

### Configuration
- OpenAI API credentials: `ekko_prototype/creds/openai_credentials.json`
- API credentials: `ekko_prototype/creds/api_credentials.json`
- Ngrok URL and token are hardcoded in `pages/app.py` (lines 27-28)

## Key Technical Details

### Path Handling
The app uses glob patterns to find files due to filesystem latency issues on Lightning.ai platform. See the `find_file()` function in `app.py` with retry logic.

### System Path Manipulation
`app.py` dynamically adds paths to sys.path to handle module imports when switching between pages (lines 15-16).

### Prompts and Resources
- Summarization prompts: `ekko_prototype/pages/tools/prompts/`
- Questions and surveys: `ekko_prototype/pages/tools/resources/`

### Current Limitations
- Authentication token is hardcoded (`chamberOfSecrets`)
- Ngrok URL needs manual updating when server restarts
- Transcription requires separate server process
- File system operations use retry logic due to Lightning.ai latency

## Testing Individual Components

```python
# Test podcast search
from ekko_prototype.pages.tools.podcast_finder import PodcastIndexSearch
searcher = PodcastIndexSearch()
results = searcher.search("tech podcasts")

# Test transcription
from ekko_prototype.pages.tools.audio_transcriber import EpisodeTranscriber
transcriber = EpisodeTranscriber()
transcript = transcriber.transcribe("path/to/audio.mp3")

# Test summarization
from ekko_prototype.pages.tools.summary_creator import TranscriptSummarizer
summarizer = TranscriptSummarizer(
    system_file_path='ekko_prototype/pages/tools/prompts/extract_wisdom_updated.md'
)
summary = summarizer.summarize_transcript("transcript text here")
```

## Important Notes
- The project is designed to run on Lightning.ai platform, which affects file operations
- Transcription can be done locally (via Whisper) or remotely (via ngrok server)
- The UI is optimized for desktop; mobile experience may have issues with sleep mode
- Feedback collection is integrated throughout for user research purposes
- always spell ekko 'ekko', all lowercase
- use proper gitflow; create & checkout branches, make commits to them, push & merge
- dont forget to backdate the commits
- always use uv to run python scripts, including streamlit  & manage the python env & the dependencies
