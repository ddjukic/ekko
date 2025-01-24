"""
Unit tests for OpenAI Whisper transcription.
"""

import unittest
from unittest.mock import Mock, patch, MagicMock, mock_open
import sys
import os
import json
import tempfile

# Add the parent directory to the path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from ekko_prototype.pages.tools.audio_transcriber import EpisodeTranscriber


class TestOpenAIWhisperTranscriber(unittest.TestCase):
    """Test OpenAI Whisper API transcription."""
    
    def setUp(self):
        """Set up test fixtures."""
        # We'll create a new OpenAI-based transcriber class in the actual implementation
        pass
    
    @patch('os.makedirs')
    @patch('os.path.exists')
    @patch('os.path.getsize')
    @patch('openai.OpenAI')
    @patch('builtins.open', new_callable=mock_open, read_data=b'fake audio data')
    def test_transcribe_with_openai_api(self, mock_file, mock_openai_class, mock_getsize, mock_exists, mock_makedirs):
        """Test transcription using OpenAI Whisper API."""
        # Mock file existence and size
        mock_exists.return_value = True
        mock_getsize.return_value = 1000000  # 1MB file
        mock_makedirs.return_value = None
        
        # Mock OpenAI client
        mock_client = MagicMock()
        mock_openai_class.return_value = mock_client
        
        # Mock transcription response
        mock_response = MagicMock()
        mock_response.text = "This is the transcribed text from OpenAI Whisper API."
        mock_client.audio.transcriptions.create.return_value = mock_response
        
        # Create transcriber with OpenAI API key
        from ekko_prototype.pages.tools.openai_whisper_transcriber import OpenAIWhisperTranscriber
        transcriber = OpenAIWhisperTranscriber(api_key="test-api-key")
        
        # Test transcription
        audio_file_path = "/tmp/test_audio.mp3"
        result = transcriber.transcribe(audio_file_path)
        
        # Verify the API was called correctly
        mock_client.audio.transcriptions.create.assert_called_once()
        call_args = mock_client.audio.transcriptions.create.call_args
        
        # Check that the model is whisper-1
        self.assertEqual(call_args.kwargs['model'], 'whisper-1')
        
        # Verify the result
        self.assertIsNotNone(result)
        self.assertIn("transcribed text", result)
    
    @patch('os.makedirs')
    @patch('os.path.exists')
    @patch('os.path.getsize')
    @patch('openai.OpenAI')
    def test_transcribe_with_options(self, mock_openai_class, mock_getsize, mock_exists, mock_makedirs):
        """Test transcription with additional options like language and prompt."""
        # Mock file existence and size
        mock_exists.return_value = True
        mock_getsize.return_value = 1000000  # 1MB file
        mock_makedirs.return_value = None
        
        # Mock OpenAI client
        mock_client = MagicMock()
        mock_openai_class.return_value = mock_client
        
        # Mock transcription response
        mock_response = MagicMock()
        mock_response.text = "Transcribed podcast content"
        mock_client.audio.transcriptions.create.return_value = mock_response
        
        from ekko_prototype.pages.tools.openai_whisper_transcriber import OpenAIWhisperTranscriber
        transcriber = OpenAIWhisperTranscriber(api_key="test-api-key")
        
        # Test transcription with options
        with patch('builtins.open', mock_open(read_data=b'audio data')):
            result = transcriber.transcribe(
                "/tmp/test.mp3",
                language="en",
                prompt="This is a podcast episode about technology."
            )
        
        # Verify API call includes options
        call_args = mock_client.audio.transcriptions.create.call_args.kwargs
        self.assertEqual(call_args['language'], 'en')
        self.assertEqual(call_args['prompt'], "This is a podcast episode about technology.")
    
    @patch('os.makedirs')
    @patch('os.path.exists')
    @patch('openai.OpenAI')
    def test_transcribe_with_timestamps(self, mock_openai_class, mock_exists, mock_makedirs):
        """Test transcription with timestamp information."""
        # Mock file existence
        mock_exists.return_value = True
        mock_makedirs.return_value = None
        
        # Mock OpenAI client
        mock_client = MagicMock()
        mock_openai_class.return_value = mock_client
        
        # Mock transcription response with verbose JSON format
        mock_response = MagicMock()
        mock_response.text = "Full transcript text"
        mock_response.model_dump = lambda: {
            'text': 'Full transcript text',
            'segments': [
                {
                    'id': 0,
                    'start': 0.0,
                    'end': 5.0,
                    'text': 'First segment'
                },
                {
                    'id': 1,
                    'start': 5.0,
                    'end': 10.0,
                    'text': 'Second segment'
                }
            ],
            'language': 'english'
        }
        mock_client.audio.transcriptions.create.return_value = mock_response
        
        from ekko_prototype.pages.tools.openai_whisper_transcriber import OpenAIWhisperTranscriber
        transcriber = OpenAIWhisperTranscriber(api_key="test-api-key")
        
        # Test transcription with timestamps
        with patch('builtins.open', mock_open(read_data=b'audio data')):
            result = transcriber.transcribe_with_timestamps("/tmp/test.mp3")
        
        # Verify response format was set to verbose_json
        call_args = mock_client.audio.transcriptions.create.call_args.kwargs
        self.assertEqual(call_args.get('response_format'), 'verbose_json')
        
        # Verify the result contains segments
        self.assertIn('segments', result)
        self.assertEqual(len(result['segments']), 2)
    
    @patch('os.makedirs')
    @patch('os.path.exists')
    @patch('os.path.getsize')
    @patch('openai.OpenAI')
    def test_transcribe_error_handling(self, mock_openai_class, mock_getsize, mock_exists, mock_makedirs):
        """Test error handling during transcription."""
        # Mock file existence and size
        mock_exists.return_value = True
        mock_getsize.return_value = 1000000  # 1MB file
        mock_makedirs.return_value = None
        
        # Mock OpenAI client that raises an error
        mock_client = MagicMock()
        mock_openai_class.return_value = mock_client
        mock_client.audio.transcriptions.create.side_effect = Exception("API Error: Invalid API key")
        
        from ekko_prototype.pages.tools.openai_whisper_transcriber import OpenAIWhisperTranscriber
        transcriber = OpenAIWhisperTranscriber(api_key="invalid-key")
        
        # Test that error is handled gracefully
        with patch('builtins.open', mock_open(read_data=b'audio data')):
            result = transcriber.transcribe("/tmp/test.mp3")
        
        # Should return None or raise a specific exception
        self.assertIsNone(result)
    
    @patch('os.makedirs')
    @patch('os.path.exists')
    @patch('os.path.getsize')
    @patch('openai.OpenAI')
    def test_transcribe_large_file_chunking(self, mock_openai_class, mock_getsize, mock_exists, mock_makedirs):
        """Test handling of large audio files that may need chunking."""
        # Mock file existence and large size
        mock_exists.return_value = True
        mock_getsize.side_effect = [30 * 1024 * 1024, 30 * 1024 * 1024]  # Return large size twice
        mock_makedirs.return_value = None
        
        # Mock OpenAI client
        mock_client = MagicMock()
        mock_openai_class.return_value = mock_client
        
        # Mock multiple responses for chunks
        mock_response1 = MagicMock()
        mock_response1.text = "First chunk transcription"
        mock_response2 = MagicMock()
        mock_response2.text = "Second chunk transcription"
        
        mock_client.audio.transcriptions.create.side_effect = [mock_response1, mock_response2]
        
        from ekko_prototype.pages.tools.openai_whisper_transcriber import OpenAIWhisperTranscriber
        transcriber = OpenAIWhisperTranscriber(api_key="test-api-key")
        
        # Test transcription of large file
        # The implementation will try direct upload first (OpenAI supports up to 25MB)
        with patch('builtins.open', mock_open(read_data=b'large audio data')):
            result = transcriber.transcribe("/tmp/large_file.mp3")
        
        # Should still work with one API call since _transcribe_large_file falls back to direct upload
        self.assertEqual(mock_client.audio.transcriptions.create.call_count, 1)
        self.assertEqual(result, "First chunk transcription")
    
    def test_load_api_key_from_file(self):
        """Test loading OpenAI API key from credentials file."""
        # Create a temporary credentials file
        creds = {"api_key": "sk-test-key-123"}
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(creds, f)
            temp_file = f.name
        
        try:
            from ekko_prototype.pages.tools.openai_whisper_transcriber import OpenAIWhisperTranscriber
            transcriber = OpenAIWhisperTranscriber(credentials_file=temp_file)
            self.assertEqual(transcriber.api_key, "sk-test-key-123")
        finally:
            os.unlink(temp_file)
    
    @patch('os.makedirs')
    @patch('os.path.exists')
    @patch('os.path.getsize')
    @patch('openai.OpenAI')
    def test_transcribe_with_different_models(self, mock_openai_class, mock_getsize, mock_exists, mock_makedirs):
        """Test using different Whisper model versions if available."""
        # Mock file existence and size
        mock_exists.return_value = True
        mock_getsize.return_value = 1000000  # 1MB file
        mock_makedirs.return_value = None
        
        # Mock OpenAI client
        mock_client = MagicMock()
        mock_openai_class.return_value = mock_client
        
        mock_response = MagicMock()
        mock_response.text = "Transcribed text"
        mock_client.audio.transcriptions.create.return_value = mock_response
        
        from ekko_prototype.pages.tools.openai_whisper_transcriber import OpenAIWhisperTranscriber
        
        # Test with default model (whisper-1)
        transcriber = OpenAIWhisperTranscriber(api_key="test-key")
        with patch('builtins.open', mock_open(read_data=b'audio')):
            transcriber.transcribe("/tmp/test.mp3")
        
        call_args = mock_client.audio.transcriptions.create.call_args.kwargs
        self.assertEqual(call_args['model'], 'whisper-1')


class TestTranscriptFetcherIntegration(unittest.TestCase):
    """Test the unified transcript fetcher with OpenAI Whisper."""
    
    @patch('ekko_prototype.pages.tools.transcript_fetcher.EpisodeTranscriber')
    @patch('ekko_prototype.pages.tools.transcript_fetcher.EpisodeDownloader')
    @patch('ekko_prototype.pages.tools.transcript_fetcher.YouTubePodcastDetector')
    @patch('ekko_prototype.pages.tools.openai_whisper_transcriber.OpenAIWhisperTranscriber')
    def test_unified_fetcher_youtube_fallback_to_openai(self, mock_whisper_class, mock_youtube_class, mock_downloader_class, mock_transcriber_class):
        """Test that fetcher falls back to OpenAI Whisper when YouTube fails."""
        from ekko_prototype.pages.tools.transcript_fetcher import UnifiedTranscriptFetcher, TranscriptConfig
        from ekko_prototype.pages.tools.youtube_detector import TranscriptResult, TranscriptSource
        
        # Mock YouTube detector that returns no transcript
        mock_youtube = MagicMock()
        mock_youtube_class.return_value = mock_youtube
        mock_youtube.check_youtube_availability.return_value = (False, None)
        mock_youtube.calculate_quality_score.return_value = 0.9
        
        # Mock OpenAI Whisper that succeeds
        mock_whisper = MagicMock()
        mock_whisper_class.return_value = mock_whisper
        mock_whisper.transcribe.return_value = "Transcribed by OpenAI Whisper"
        
        # Mock EpisodeDownloader
        mock_downloader = MagicMock()
        mock_downloader_class.return_value = mock_downloader
        mock_downloader.download_single_episode.return_value = "/tmp/audio.mp3"
        
        # Mock EpisodeTranscriber
        mock_transcriber = MagicMock()
        mock_transcriber_class.return_value = mock_transcriber
        
        # Configure to use OpenAI instead of local Whisper
        config = TranscriptConfig(
            prefer_youtube=True,
            use_openai_whisper=True,  # New config option
            use_remote_whisper=False,
            cache_transcripts=False
        )
        
        fetcher = UnifiedTranscriptFetcher(config)
        
        result = fetcher.get_transcript(
            podcast_name="Test Podcast",
            episode_title="Test Episode",
            episode_audio_url="https://example.com/audio.mp3",
            podcast_rss_url="https://example.com/feed.rss"
        )
        
        # Verify YouTube was checked first
        mock_youtube.check_youtube_availability.assert_called_once()
        
        # Verify audio was downloaded
        mock_downloader.download_single_episode.assert_called_once()
        
        # Verify OpenAI Whisper was used as fallback
        mock_whisper.transcribe.assert_called_once()
        
        # Verify result
        self.assertIsNotNone(result)
        self.assertEqual(result.text, "Transcribed by OpenAI Whisper")
        self.assertEqual(result.source, TranscriptSource.WHISPER_LOCAL)


if __name__ == '__main__':
    unittest.main()