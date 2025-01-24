"""
OpenAI Whisper API transcriber for ekko.

This module provides transcription using OpenAI's Whisper API instead of
local Hugging Face models.
"""

import os
import json
import logging
from typing import Optional, Dict, Any, List
from pathlib import Path

import openai
from openai import OpenAI

logger = logging.getLogger(__name__)


class OpenAIWhisperTranscriber:
    """Transcribe audio using OpenAI's Whisper API."""
    
    # Maximum file size for OpenAI API (25 MB)
    MAX_FILE_SIZE = 25 * 1024 * 1024  # 25 MB in bytes
    
    def __init__(
        self,
        api_key: Optional[str] = None,
        credentials_file: Optional[str] = None,
        parent_folder: str = "./transcripts",
        model: str = "whisper-1"
    ):
        """
        Initialize the OpenAI Whisper transcriber.
        
        Args:
            api_key: OpenAI API key (if not provided, will look in credentials_file)
            credentials_file: Path to JSON file containing API credentials
            parent_folder: Directory to save transcripts
            model: OpenAI Whisper model to use (default: whisper-1)
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
    
    def _load_api_key(self, credentials_file: Optional[str]) -> Optional[str]:
        """Load API key from credentials file."""
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
            with open(credentials_file, 'r') as f:
                creds = json.load(f)
                return creds.get('api_key')
        except Exception as e:
            logger.error(f"Failed to load API key from {credentials_file}: {e}")
            return None
    
    def transcribe(
        self,
        audio_file_path: str,
        language: Optional[str] = None,
        prompt: Optional[str] = None,
        temperature: float = 0.0
    ) -> Optional[str]:
        """
        Transcribe an audio file using OpenAI Whisper API.
        
        Args:
            audio_file_path: Path to the audio file
            language: Language of the audio (ISO-639-1 format)
            prompt: Optional prompt to guide the transcription
            temperature: Sampling temperature (0-1)
            
        Returns:
            Transcribed text or None if failed
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
        language: Optional[str] = None,
        prompt: Optional[str] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Transcribe with timestamp information.
        
        Args:
            audio_file_path: Path to the audio file
            language: Language of the audio
            prompt: Optional prompt to guide transcription
            
        Returns:
            Dictionary with transcript and segments with timestamps
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
        language: Optional[str] = None,
        prompt: Optional[str] = None,
        temperature: float = 0.0
    ) -> Optional[str]:
        """
        Transcribe large files by chunking them.
        
        Note: This is a simplified implementation. In production, you'd want
        to use proper audio processing libraries to split at silence points.
        """
        logger.warning("Large file chunking not fully implemented. Attempting direct upload.")
        
        # For now, just try to transcribe directly and let the API handle it
        # OpenAI API actually supports files up to 25MB
        try:
            return self.transcribe(audio_file_path, language, prompt, temperature)
        except Exception as e:
            logger.error(f"Failed to transcribe large file: {e}")
            return None
    
    def _should_chunk_file(self, file_path: str) -> bool:
        """Check if file needs to be chunked."""
        return os.path.getsize(file_path) > self.MAX_FILE_SIZE
    
    def _chunk_audio_file(self, file_path: str) -> List[str]:
        """
        Chunk audio file into smaller pieces.
        
        Note: This would require audio processing libraries like pydub.
        For now, returning empty list as placeholder.
        """
        logger.warning("Audio chunking not implemented")
        return []
    
    def _save_transcript(self, transcript_text: str, audio_file_path: str) -> str:
        """Save transcript to a text file."""
        audio_filename = os.path.basename(audio_file_path)
        title = os.path.splitext(audio_filename)[0]
        output_file = os.path.join(self.parent_folder, f"{title}.txt")
        
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(transcript_text)
        
        return output_file
    
    def translate(
        self,
        audio_file_path: str,
        prompt: Optional[str] = None
    ) -> Optional[str]:
        """
        Translate audio to English using OpenAI Whisper API.
        
        Args:
            audio_file_path: Path to the audio file
            prompt: Optional prompt to guide translation
            
        Returns:
            Translated English text or None if failed
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