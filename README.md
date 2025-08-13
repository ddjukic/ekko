# ekko

AI-powered podcast discovery, transcription, and summarization platform.

## 🎯 Overview

ekko is a modern Python application that helps users discover, transcribe, and summarize podcast content using state-of-the-art AI technologies. It features intelligent transcript fetching, CrewAI-powered agent workflows, and a user-friendly Streamlit interface.

## ✨ Features

- **Smart Transcript Fetching**: Automatically checks YouTube for existing transcripts before transcribing
- **AI-Powered Summarization**: Uses GPT-4 to create comprehensive, actionable summaries
- **Interactive Chat**: RAG-based chat interface for exploring podcast content
- **Multi-Source Support**: Works with RSS feeds, YouTube videos, and direct audio files
- **Rate Limiting**: Demo mode with configurable usage limits
- **Professional Architecture**: Built with modern Python practices, type hints, and comprehensive testing

## 🚀 Quick Start

### Prerequisites

- Python 3.13+
- uv package manager
- OpenAI API key
- (Optional) YouTube API key for enhanced search

### Installation

1. **Clone the repository**
```bash
git clone https://github.com/ekko-ai/ekko.git
cd ekko
```

2. **Install uv** (if not already installed)
```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

3. **Set up environment**
```bash
# Install dependencies
make install

# Or manually with uv
uv python install 3.13
uv sync
```

4. **Configure environment variables**
```bash
cp .env.example .env
# Edit .env with your API keys
```

5. **Run the application**
```bash
make run

# Or manually
uv run streamlit run ekko_prototype/landing.py
```

## 🛠️ Development

### Setup Development Environment

```bash
# Install all dependencies including dev tools
make dev-install

# Run tests
make test

# Run linting
make lint

# Format code
make format
```

### Project Structure

```
ekko/
├── ekko_prototype/          # Main Streamlit application
│   ├── landing.py          # Entry point
│   ├── pages/              # Streamlit pages
│   │   ├── app.py         # Main app interface
│   │   └── tools/         # Core functionality
│   └── agents/            # CrewAI agents
├── rss_parser/            # RSS feed parsing module
├── docs/                  # Documentation
├── tests/                 # Test suite
└── docker/               # Docker configuration
```

## 🐳 Docker Deployment

```bash
# Build Docker image
make docker-build

# Run locally
make docker-run

# Deploy to Google Cloud Run
make deploy
```

## 📚 Documentation

- [uv Package Manager Guide](docs/how_to_uv.md)
- [YouTube Transcript Extraction](docs/yt_dlp_guide.md)
- [CrewAI Agent Framework](docs/crewAI_101.md)
- [API Documentation](docs/api.md)

## 🧪 Testing

```bash
# Run all tests
make test

# Run with coverage
make test-coverage

# Run specific test file
uv run pytest tests/test_specific.py
```

## 🔒 Security

- Environment variables for sensitive data
- Rate limiting for API protection
- Input validation and sanitization
- Regular dependency updates

## 🤝 Contributing

We welcome contributions! Please see our [Contributing Guide](CONTRIBUTING.md) for details.

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'feat: add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- OpenAI for GPT-4 API
- Streamlit for the amazing web framework
- CrewAI for agent orchestration
- The open-source community

## 📞 Contact

- GitHub: [@ekko-ai](https://github.com/ekko-ai/ekko)
- Email: team@ekko.ai
- Documentation: [docs.ekko.ai](https://docs.ekko.ai)

---

## 🗺️ Roadmap

### Completed ✅
- Chat functionality
- Episode length metadata
- Local Whisper execution & ngrok server
- Search functionality improvement
- Survey questions for feedback

### In Progress 🚧
- Migration to uv package manager
- CrewAI agent integration
- YouTube transcript fetching
- Authentication and rate limiting
- Docker deployment setup

### Planned 📋
- Audio playback through quotes (needs timestamps)
- Chat with quote/idea/habit functionality
- Transcripts with diarization (speaker recognition)
- Audio summaries with synthesized voice
- Enhanced personalization features

## 🏗️ Architecture Decisions

- **uv**: Fast, modern Python package management
- **CrewAI**: Intelligent agent orchestration for complex workflows
- **Streamlit**: Rapid prototyping and user-friendly interface
- **Docker**: Containerized deployment for consistency
- **Google Cloud Run**: Serverless, scalable hosting

---

Built with ❤️ by the ekko team
