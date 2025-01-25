import json
import os
import sys
from collections.abc import Generator

import streamlit as st
from openai import OpenAI

# Add parent directory to path for imports
parent_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)

from config import config


# TODO:
# - rename the 'system_content' and everything related to something more descriptive,
# like 'pattern' or whatever
class TranscriptSummarizer:
    """
    Summarizes podcast transcripts using the OpenAI API.
    
    :ivar model: The OpenAI model to use for summarization
    :vartype model: str
    :ivar system_content: The system prompt content
    :vartype system_content: str
    :ivar api_key: OpenAI API key
    :vartype api_key: str
    :ivar client: OpenAI client instance
    :vartype client: OpenAI
    """

    def __init__(self, model: str = "gpt-4o", system_file_path: str = "system.md", 
                 credentials_file_path: str | None = None):
        """
        Initialize the summarizer with the specified model, system file, and credentials file.
        
        :param model: The OpenAI model to use for summarization
        :type model: str
        :param system_file_path: Path to the markdown file containing system prompt
        :type system_file_path: str
        :param credentials_file_path: Optional path to JSON file with API key
        :type credentials_file_path: Optional[str]
        """
        self.model = model
        self.system_content = self._load_system_content(system_file_path)
        
        # Try environment variable first, then JSON file
        if credentials_file_path and os.path.exists(credentials_file_path):
            self.api_key = self._load_api_key_from_file(credentials_file_path)
        else:
            self.api_key = config.OPENAI_API_KEY
            
        self.client = OpenAI(api_key=self.api_key)

    def _load_system_content(self, file_path: str) -> str:
        """
        Load the system context from a markdown file.
        
        :param file_path: Path to the markdown file containing system context
        :type file_path: str
        
        :return: Content of the system context file
        :rtype: str
        """
        with open(file_path, encoding='utf-8') as file:
            return file.read()

    def _load_api_key_from_file(self, file_path: str) -> str:
        """
        Load the OpenAI API key from a JSON file.
        
        :param file_path: Path to the JSON file containing the OpenAI API key
        :type file_path: str
        
        :return: The OpenAI API key
        :rtype: str
        """
        with open(file_path) as file:
            credentials = json.load(file)
            return credentials['api_key']

    def summarize_transcript(self, transcript: str) -> Generator[str]:
        """
        Summarize the provided transcript using the OpenAI API.
        
        :param transcript: The transcript text to summarize
        :type transcript: str
        
        :yields: Chunks of the summary as they are generated
        :rtype: Generator[str, None, None]
        
        :raises Exception: If API call fails (caught and displayed in Streamlit)
        """
        system_message = {"role": "system", "content": self.system_content}
        user_message = {"role": "user", "content": transcript}
        messages = [system_message, user_message]


        try:
            response_stream = self.client.chat.completions.create(model=self.model,
            messages=messages,
            temperature=0.0,
            top_p=1,
            frequency_penalty=0.1,
            presence_penalty=0.1,
            stream=True
            )
        except Exception as e:
            st.error(e)

        for chunk in response_stream:
            if chunk.choices[0].delta.content is not None:
                yield chunk.choices[0].delta.content

        
# Example usage:
# summarizer = TranscriptSummarizer()
# for summary_part in summarizer.summarize_transcript("Here is some transcript text..."):
#     print(summary_part)  # Or integrate with streaming in a web app
