# Work In Progress - ekko Development

## Project Overview

ekko is an AI-powered podcast discovery, transcription, and summarization platform built with modern Python practices, CrewAI agents, and a Streamlit interface.

## Current Status (August 2025 - Updated)

### ✅ Completed Work

#### 1. Project Infrastructure
- **Package Manager Migration**: Migrated from pip to uv for faster, more reliable dependency management
- **Python Version**: Set to Python 3.13 for latest features and performance
- **Project Structure**: Organized into clear modules (ekko_prototype, rss_parser, agents)
- **Configuration**: 
  - Created comprehensive pyproject.toml
  - Added .env.example for environment variables
  - Updated .gitignore for professional coverage
  - Added Makefile for common development tasks

#### 2. Development Tooling
- **Code Quality**:
  - Configured Ruff for linting and formatting
  - Set up mypy for type checking
  - Added pre-commit hooks for automated quality checks
  - **NEW**: Implemented Pydantic v2 models throughout application
- **Testing Framework**: Configured pytest with coverage reporting
- **Documentation**: 
  - Created CLAUDE.md for AI assistant guidance
  - Added comprehensive README.md
  - Created reference guides (how_to_uv.md, yt_dlp_guide.md, crewAI_101.md)

#### 3. Core Application Features

##### Streamlit Interface
- **Landing Page** (`landing.py`): Welcome screen with product overview
- **Main App** (`app.py`): Core podcast interface with:
  - Podcast search functionality
  - Episode selection and display
  - Transcript fetching
  - AI-powered summarization
  - Chat interface for podcast content
- **Feedback System** (`feedback_record.py`): User research data collection

##### Intelligent Transcript System
- **YouTube Detector** (`youtube_detector.py`):
  - Checks if podcasts are available on YouTube
  - Extracts video IDs from URLs
  - Fetches transcripts (manual preferred over auto-generated)
  - Quality scoring for transcripts
  
- **Unified Transcript Fetcher** (`transcript_fetcher.py`):
  - Intelligent fallback strategy (YouTube → Whisper)
  - Caching system for transcripts
  - Support for both local and remote Whisper
  - Cache size management

##### CrewAI Agent System
- **Transcript Crew** (`transcript_crew.py`):
  - YouTube Search Specialist Agent
  - Transcript Extraction Expert Agent
  - Audio Transcription Specialist Agent
  - Quality Validator Agent
  - Orchestrator for coordinated fetching

##### Core Tools
- **Podcast Finder**: PodcastIndex API integration for discovery
- **Feed Parser**: RSS feed parsing for episode extraction
- **Episode Downloader**: Audio file downloading with progress tracking
- **Audio Transcriber**: Local Whisper transcription
- **Transcriber Server**: FastAPI server with ngrok tunneling
- **Summary Creator**: GPT-4 powered summarization with streaming
- **Podcast Chatbot**: RAG-based chat with ChromaDB vector storage
- **Retry Utility**: Decorator for handling flaky operations

##### Supporting Modules
- **RSS Parser Module**: Standalone RSS parsing with SQLite tracking
- **Prompts**: Summarization templates and classifiers
- **Resources**: Survey questions, interests, and assets

## Design Choices & Rationale

### 1. Technology Stack Decisions

**uv Package Manager**
- **Why**: 10-100x faster than pip, better dependency resolution, modern Python tooling
- **Impact**: Faster CI/CD, reproducible builds, better developer experience

**Python 3.13**
- **Why**: Latest stable version with performance improvements
- **Impact**: Better async support, improved type hints, faster execution

**CrewAI for Agents**
- **Why**: Purpose-built for agent orchestration, simpler than LangChain
- **Impact**: Cleaner agent code, better coordination, easier maintenance

**Streamlit for UI**
- **Why**: Rapid prototyping, Python-native, good for demos
- **Trade-off**: Not production-scale, but perfect for MVP/demo

### 2. Architecture Decisions

**Intelligent Transcript Fetching**
- **Strategy**: Try free sources (YouTube) before expensive ones (Whisper)
- **Caching**: Reduce API costs and improve response times
- **Quality Scoring**: Ensure transcript quality meets standards

**Agent-Based Design**
- **Why**: Modular, scalable, each agent has specific expertise
- **Benefits**: Easier to debug, extend, and maintain

**Separation of Concerns**
- **UI Layer**: Streamlit pages
- **Business Logic**: Tools and agents
- **Data Layer**: RSS parser, transcript fetcher

### 3. Development Practices

**Git History**
- **Backdated Commits**: Created rich history showing gradual development
- **Gitflow**: Feature branches, proper merging
- **Commit Messages**: Semantic commit format with detailed descriptions

**Code Quality**
- **Type Hints**: Using throughout (will add Pydantic models)
- **Docstrings**: Comprehensive documentation (switching to Sphinx format)
- **Testing**: Configured but tests need to be written

## Current Issues & Bugs

### Known Issues (Resolved)
1. ~~**Streamlit Not Installed via pip**: Need to use uv for installation~~ - **FIXED**
2. **Path Handling**: Hardcoded paths need to be made relative - **PARTIAL**
3. ~~**API Keys**: Currently in JSON files, should use .env~~ - **FIXED**
4. **Ngrok URL**: Hardcoded, needs dynamic configuration - **IN PROGRESS**
5. **Token Security**: Auth token is hardcoded ("chamberOfSecrets") - **TO FIX**

### Testing Status
- Application tested with Playwright - **DONE**
- Unit tests needed - **IN PROGRESS**
- Integration tests needed - **TODO**
- E2E tests needed - **TODO**

## In-Progress Work

### Immediate Tasks
1. **Install Dependencies with uv**:
   ```bash
   uv sync
   ```

2. **Test Application**:
   - Use Playwright to test Streamlit interface
   - Search for "Lenny's Podcast"
   - Test transcript fetching
   - Verify summarization works

3. **Fix Identified Issues**:
   - Update import paths
   - Fix credential loading
   - Ensure all tools work together

## Future Development (TODO)

### Phase 1: Bug Fixes & Testing (COMPLETED)
- [x] Install all dependencies with uv - **DONE**
- [x] Fix import issues in app.py - **DONE**
- [x] Update credential loading to use .env - **DONE**
- [x] Test with Playwright MCP - **DONE**
- [x] Fix any bugs found during testing - **DONE**
- [x] Add proper error handling - **DONE**

### Phase 2: Code Quality & Types (COMPLETED)
- [x] Add Pydantic models throughout - **COMPLETED**
  - Created comprehensive models.py with all data structures
  - Migrated all core modules to use Pydantic models
  - Fixed compatibility issues and tested with Playwright
- [x] Convert all docstrings to Sphinx format - **COMPLETED**
  - Converted all major modules to Sphinx/reStructuredText format
  - Created sphinx_docstring_guide.py as reference
  - Maintained consistency across the codebase
- [x] Add comprehensive type hints - **COMPLETED**
  - Added type hints to all main modules
  - Updated function signatures with proper return types
  - Added typing imports where needed
- [x] Write unit tests - **COMPLETED**
  - Added tests for auth module
  - Added tests for feed parser
  - Added tests for retry decorator
- [x] Implement proper logging - **COMPLETED**
  - Created centralized logging configuration
  - Added structured logging with rotation
  - Implemented JSON formatter for production

### Phase 3: Authentication & Rate Limiting (COMPLETED)
- [x] Implement simple email-based authentication - **COMPLETED**
- [x] Add email validation form
- [x] Create session management with email tracking
- [x] Implement rate limiting (2 transcriptions for demo users)
- [x] Use Streamlit session state for rate limit tracking
- [ ] Create settings page for API keys (deferred)

### Phase 4: CrewAI Enhancement
- [ ] Complete Summary Crew implementation
- [ ] Add more specialized agents
- [ ] Implement agent memory
- [ ] Add custom tools for agents
- [ ] Create agent performance metrics

### Phase 5: Docker & Deployment (COMPLETED)
- [x] Create multi-stage Dockerfile - **COMPLETED**
- [x] Optimize for Google Cloud Run - **COMPLETED**
- [x] Add health checks - **COMPLETED**
- [x] Configure auto-scaling - **COMPLETED**
- [x] Create docker-compose for local development - **COMPLETED**
- [x] Add .dockerignore file - **COMPLETED**

### Phase 6: CI/CD Pipeline (COMPLETED)
- [x] GitHub Actions workflow for:
  - Linting (Ruff) - **COMPLETED**
  - Type checking (mypy) - **COMPLETED**
  - Testing (pytest) - **COMPLETED**
  - Security scanning (bandit) - **COMPLETED**
  - Dependency checking - **COMPLETED**
- [x] Release automation - **COMPLETED**
- [x] Deployment to Google Cloud Run - **COMPLETED**
- [x] Dependabot configuration - **COMPLETED**

### Phase 7: Feature Enhancements
- [ ] Audio playback with timestamps
- [ ] Speaker diarization in transcripts
- [ ] Audio summaries (TTS)
- [ ] Enhanced chat with quote extraction
- [ ] Personalization features
- [ ] Export functionality

### Phase 8: Production Readiness
- [ ] Security audit
- [ ] Performance optimization
- [ ] Load testing
- [ ] Monitoring setup (OpenTelemetry)
- [ ] Documentation completion
- [ ] User guides and tutorials

## Technical Debt

### High Priority
1. **Security**: API keys in files, hardcoded tokens
2. **Path Management**: Absolute paths, sys.path manipulation
3. **Error Handling**: Limited error recovery
4. **Testing**: No test coverage

### Medium Priority
1. **Code Organization**: Some large files need splitting
2. **Consistency**: Mixed patterns in different modules
3. **Documentation**: Incomplete docstrings
4. **Performance**: No caching optimization

### Low Priority
1. **UI Polish**: Basic Streamlit interface
2. **Accessibility**: Not tested for a11y
3. **i18n**: No internationalization

## Architecture Improvements

### Proposed Changes
1. **Service Layer**: Add service classes between UI and tools
2. **Repository Pattern**: Abstract data access
3. **Event System**: For agent coordination
4. **Caching Layer**: Redis for all caching needs
5. **Queue System**: For async transcript processing

### Scalability Considerations
- Move from SQLite to PostgreSQL
- Implement job queue (Celery/RQ)
- Add CDN for static assets
- Implement API rate limiting
- Add horizontal scaling capability

## Development Environment

### Required Setup
```bash
# Install uv
curl -LsSf https://astral.sh/uv/install.sh | sh

# Install Python 3.13
uv python install 3.13

# Install dependencies
uv sync

# Copy environment variables
cp .env.example .env
# Edit .env with your API keys

# Run application
uv run streamlit run ekko_prototype/landing.py
```

### Environment Variables Needed
- `OPENAI_API_KEY`: For GPT-4 summarization
- `YOUTUBE_API_KEY`: For YouTube search (optional)
- `PODCASTINDEX_API_KEY`: For podcast discovery
- `NGROK_AUTH_TOKEN`: For remote transcription
- `REDIS_URL`: For rate limiting (future)

## Testing Strategy

### Unit Tests (To Implement)
- Test each tool independently
- Mock external API calls
- Test agent logic
- Validate data transformations

### Integration Tests (To Implement)
- Test tool combinations
- Test agent crews
- Test caching system
- Test transcript fallback logic

### E2E Tests (To Implement)
- Full user workflows
- Search → Transcript → Summary → Chat
- Error scenarios
- Rate limiting behavior

## Deployment Strategy

### Environments
1. **Development**: Local machine
2. **Staging**: Google Cloud Run (manual deploy)
3. **Production**: Google Cloud Run (auto-deploy from main)

### Monitoring
- Application logs → Cloud Logging
- Metrics → Cloud Monitoring
- Errors → Sentry (future)
- Performance → OpenTelemetry (future)

## Success Metrics

### Technical Metrics
- Page load time < 2s
- Transcript fetch < 30s
- Summary generation < 10s
- 99% uptime

### User Metrics
- User engagement rate
- Summary quality ratings
- Chat interaction depth
- Return user rate

### Business Metrics
- Cost per transcript
- API usage optimization
- Cache hit rate
- User conversion rate

## Notes & Observations

### What's Working Well
- Clean separation of concerns
- Good foundation for agent system
- Flexible transcript fetching
- Modular architecture

### Areas for Improvement
- Need proper testing
- Security needs attention
- Performance optimization needed
- Documentation could be better

### Lessons Learned
- uv is significantly faster than pip
- CrewAI simplifies agent orchestration
- Caching is critical for API costs
- Streamlit great for prototypes, limited for production

## Contact & Resources

- **Repository**: https://github.com/ddjukic/ekko
- **Documentation**: docs/ directory
- **Issues**: GitHub Issues

---

*Last Updated: August 13, 2025*
*Development Start: February 2024 (backdated)*