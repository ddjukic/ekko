"""
OpenAI Whisper API transcriber for ekko.

This module provides transcription using OpenAI's Whisper API instead of
local Hugging Face models.
"""

import json
import logging
import os
from typing import Any

from openai import OpenAI

logger = logging.getLogger(__name__)


class OpenAIWhisperTranscriber:
    """
    Transcribe audio using OpenAI's Whisper API.
    """
    
    # Maximum file size for OpenAI API (25 MB)
    MAX_FILE_SIZE = 25 * 1024 * 1024  # 25 MB in bytes
    
    def __init__(
        self,
        api_key: str | None = None,
        credentials_file: str | None = None,
        parent_folder: str = "./transcripts",
        model: str = "whisper-1"
    ):
        """
        Initialize the OpenAI Whisper transcriber.
        
        :param api_key: OpenAI API key (if not provided, will look in credentials_file)
        :type api_key: Optional[str]
        :param credentials_file: Path to JSON file containing API credentials
        :type credentials_file: Optional[str]
        :param parent_folder: Directory to save transcripts
        :type parent_folder: str
        :param model: OpenAI Whisper model to use (default: whisper-1)
        :type model: str
        """
        self.parent_folder = parent_folder
        os.makedirs(self.parent_folder, exist_ok=True)
        self.model = model
        
        # Get API key
        self.api_key = api_key or self._load_api_key(credentials_file)
        if not self.api_key:
            raise ValueError("OpenAI API key required. Provide via api_key or credentials_file.")
        
        # Initialize OpenAI client
        self.client = OpenAI(api_key=self.api_key)
        logger.info(f"Initialized OpenAI Whisper transcriber with model: {model}")
    
    def _load_api_key(self, credentials_file: str | None) -> str | None:
        """
        Load API key from credentials file.
        
        :param credentials_file: Path to credentials file
        :type credentials_file: Optional[str]
        
        :return: API key or None if not found
        :rtype: Optional[str]
        """
        if not credentials_file:
            # Try default location
            default_path = os.path.join(
                os.path.dirname(__file__), 
                '..', '..', 'creds', 'openai_credentials.json'
            )
            if os.path.exists(default_path):
                credentials_file = default_path
            else:
                return None
        
        try:
            with open(credentials_file) as f:
                creds = json.load(f)
                return creds.get('api_key')
        except Exception as e:
            logger.error(f"Failed to load API key from {credentials_file}: {e}")
            return None
    
    def transcribe(
        self,
        audio_file_path: str,
        language: str | None = None,
        prompt: str | None = None,
        temperature: float = 0.0
    ) -> str | None:
        """
        Transcribe an audio file using OpenAI Whisper API.
        
        :param audio_file_path: Path to the audio file
        :type audio_file_path: str
        :param language: Language of the audio (ISO-639-1 format)
        :type language: Optional[str]
        :param prompt: Optional prompt to guide the transcription
        :type prompt: Optional[str]
        :param temperature: Sampling temperature (0-1)
        :type temperature: float
        
        :return: Transcribed text or None if failed
        :rtype: Optional[str]
        """
        try:
            if not os.path.exists(audio_file_path):
                logger.error(f"Audio file not found: {audio_file_path}")
                return None
            
            # Check file size
            file_size = os.path.getsize(audio_file_path)
            if file_size > self.MAX_FILE_SIZE:
                logger.warning(f"File size {file_size} exceeds limit, will need chunking")
                return self._transcribe_large_file(audio_file_path, language, prompt, temperature)
            
            logger.info(f"Transcribing {audio_file_path} with OpenAI Whisper API")
            
            # Open and transcribe the audio file
            with open(audio_file_path, "rb") as audio_file:
                # Build API parameters
                params = {
                    "model": self.model,
                    "file": audio_file,
                    "temperature": temperature
                }
                
                if language:
                    params["language"] = language
                if prompt:
                    params["prompt"] = prompt
                
                # Call OpenAI API
                response = self.client.audio.transcriptions.create(**params)
                
                transcript_text = response.text
                logger.info(f"Successfully transcribed {len(transcript_text)} characters")
                
                # Save transcript to file
                transcript_path = self._save_transcript(transcript_text, audio_file_path)
                logger.info(f"Saved transcript to {transcript_path}")
                
                return transcript_text
                
        except Exception as e:
            logger.error(f"Error transcribing with OpenAI API: {e}")
            return None
    
    def transcribe_with_timestamps(
        self,
        audio_file_path: str,
        language: str | None = None,
        prompt: str | None = None
    ) -> dict[str, Any] | None:
        """
        Transcribe with timestamp information.
        
        :param audio_file_path: Path to the audio file
        :type audio_file_path: str
        :param language: Language of the audio
        :type language: Optional[str]
        :param prompt: Optional prompt to guide transcription
        :type prompt: Optional[str]
        
        :return: Dictionary with transcript and segments with timestamps
        :rtype: Optional[Dict[str, Any]]
        """
        try:
            if not os.path.exists(audio_file_path):
                logger.error(f"Audio file not found: {audio_file_path}")
                return None
            
            logger.info(f"Transcribing with timestamps: {audio_file_path}")
            
            with open(audio_file_path, "rb") as audio_file:
                params = {
                    "model": self.model,
                    "file": audio_file,
                    "response_format": "verbose_json"  # Get detailed output
                }
                
                if language:
                    params["language"] = language
                if prompt:
                    params["prompt"] = prompt
                
                response = self.client.audio.transcriptions.create(**params)
                
                # Convert response to dict
                result = response.model_dump() if hasattr(response, 'model_dump') else {
                    'text': response.text,
                    'segments': []
                }
                
                logger.info(f"Transcribed with {len(result.get('segments', []))} segments")
                return result
                
        except Exception as e:
            logger.error(f"Error getting timestamps: {e}")
            return None
    
    def _transcribe_large_file(
        self,
        audio_file_path: str,
        language: str | None = None,
        prompt: str | None = None,
        temperature: float = 0.0
    ) -> str | None:
        """
        Handle large files that exceed OpenAI's 25MB limit.
        
        .. note::
           For now, we'll return None and log an error since proper audio chunking
           requires additional dependencies like pydub and ffmpeg.
        
        :param audio_file_path: Path to the audio file
        :type audio_file_path: str
        :param language: Language of the audio
        :type language: Optional[str]
        :param prompt: Optional prompt to guide transcription
        :type prompt: Optional[str]
        :param temperature: Sampling temperature
        :type temperature: float
        
        :return: Transcribed text or None for large files
        :rtype: Optional[str]
        """
        file_size_mb = os.path.getsize(audio_file_path) / (1024 * 1024)
        logger.error(f"File size {file_size_mb:.1f}MB exceeds OpenAI's 25MB limit")
        logger.error("Audio file is too large for OpenAI Whisper API. Please use a shorter episode or enable local transcription.")
        
        # Return None to indicate failure
        # In a production system, you would:
        # 1. Use pydub to split the audio into <25MB chunks
        # 2. Transcribe each chunk
        # 3. Concatenate the results
        return None
    
    def _should_chunk_file(self, file_path: str) -> bool:
        """
        Check if file needs to be chunked.
        
        :param file_path: Path to the file
        :type file_path: str
        
        :return: True if file exceeds size limit
        :rtype: bool
        """
        return os.path.getsize(file_path) > self.MAX_FILE_SIZE
    
    def _chunk_audio_file(self, file_path: str) -> list[str]:
        """
        Chunk audio file into smaller pieces.
        
        .. note::
           This would require audio processing libraries like pydub.
           For now, returning empty list as placeholder.
        
        :param file_path: Path to the audio file
        :type file_path: str
        
        :return: List of chunk file paths
        :rtype: List[str]
        """
        logger.warning("Audio chunking not implemented")
        return []
    
    def _save_transcript(self, transcript_text: str, audio_file_path: str) -> str:
        """
        Save transcript to a text file.
        
        :param transcript_text: The transcript text to save
        :type transcript_text: str
        :param audio_file_path: Path to the original audio file
        :type audio_file_path: str
        
        :return: Path to the saved transcript file
        :rtype: str
        """
        audio_filename = os.path.basename(audio_file_path)
        title = os.path.splitext(audio_filename)[0]
        output_file = os.path.join(self.parent_folder, f"{title}.txt")
        
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(transcript_text)
        
        return output_file
    
    def translate(
        self,
        audio_file_path: str,
        prompt: str | None = None
    ) -> str | None:
        """
        Translate audio to English using OpenAI Whisper API.
        
        :param audio_file_path: Path to the audio file
        :type audio_file_path: str
        :param prompt: Optional prompt to guide translation
        :type prompt: Optional[str]
        
        :return: Translated English text or None if failed
        :rtype: Optional[str]
        """
        try:
            if not os.path.exists(audio_file_path):
                logger.error(f"Audio file not found: {audio_file_path}")
                return None
            
            logger.info(f"Translating {audio_file_path} to English")
            
            with open(audio_file_path, "rb") as audio_file:
                params = {
                    "model": self.model,
                    "file": audio_file
                }
                
                if prompt:
                    params["prompt"] = prompt
                
                response = self.client.audio.translations.create(**params)
                
                translated_text = response.text
                logger.info(f"Successfully translated {len(translated_text)} characters")
                
                return translated_text
                
        except Exception as e:
            logger.error(f"Error translating with OpenAI API: {e}")
            return None