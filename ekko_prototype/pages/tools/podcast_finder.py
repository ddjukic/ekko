import hashlib
import json
import os
import sys
import time
from typing import Any

import requests

# Add parent directory to path for imports
parent_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)

from config import config
from models import PodcastModel


class PodcastIndexSearch:
    """
    A class to interact with the PodcastIndex API to search for podcasts.
    
    :ivar api_key: The API key for the PodcastIndex service
    :vartype api_key: str
    :ivar api_secret: The API secret for the PodcastIndex service
    :vartype api_secret: str
    :ivar base_url: Base URL for the PodcastIndex API
    :vartype base_url: str
    """
    def __init__(self, api_credentials_path: str | None = None):
        """
        Initialize the PodcastIndexSearch class by loading the API credentials.
        
        :param api_credentials_path: Optional path to JSON file with credentials
        :type api_credentials_path: Optional[str]
        """
        self.load_api_credentials(api_credentials_path)
        self.base_url = "https://api.podcastindex.org/api/1.0/search/byterm?q="

    def load_api_credentials(self, path: str | None = None) -> dict[str, str]:
        """
        Load the API key and secret from environment variables or JSON file.
        
        :param path: Optional path to the JSON file containing credentials
        :type path: Optional[str]
        
        :return: Dictionary with 'success' or 'error' key and corresponding message
        :rtype: Dict[str, str]
        """
        # First try environment variables
        self.api_key = config.PODCASTINDEX_API_KEY
        self.api_secret = config.PODCASTINDEX_API_SECRET
        
        if self.api_key and self.api_secret:
            return {'success': 'API credentials loaded from environment.'}
        
        # Fallback to JSON file if provided
        if path:
            try:
                with open(path) as file:
                    credentials = json.load(file)
                    self.api_key = credentials.get('api_key', '')
                    self.api_secret = credentials.get('api_secret', '')
                    return {'success': 'API credentials loaded from file.'}
            except FileNotFoundError:
                return {'error': f'File not found: {path}'}
            except Exception as e:
                return {'error': str(e)}
        
        return {'error': 'No API credentials found'}

    def generate_auth_headers(self) -> dict[str, str]:
        """
        Generate the necessary authentication headers for the request.
        
        :return: Dictionary containing authentication headers
        :rtype: Dict[str, str]
        """
        epoch_time = int(time.time())
        data_to_hash = self.api_key + self.api_secret + str(epoch_time)
        sha_1 = hashlib.sha1(data_to_hash.encode()).hexdigest()

        return {
            'X-Auth-Date': str(epoch_time),
            'X-Auth-Key': self.api_key,
            'Authorization': sha_1,
            'User-Agent': 'postcasting-index-python-cli',
        }

    def parse_search_results(self, results: dict[str, Any]) -> list[PodcastModel]:
        """
        Parse the search results to extract relevant podcast information.
        
        :param results: The raw search results from the API
        :type results: Dict[str, Any]
        
        :return: List of parsed podcast models
        :rtype: List[PodcastModel]
        """
        podcasts = []
        for feed in results.get('feeds', []):
            try:
                podcast = PodcastModel(
                    id=feed.get('id', 0),
                    title=feed.get('title', ''),
                    url=feed.get('url', ''),
                    description=feed.get('description'),
                    author=feed.get('author'),
                    image=feed.get('image'),
                    categories=feed.get('categories', {}).values() if isinstance(feed.get('categories'), dict) else [],
                    language=feed.get('language'),
                    explicit=feed.get('explicit', False)
                )
                podcasts.append(podcast)
            except Exception as e:
                # Skip invalid podcast entries
                print(f"Error parsing podcast: {e}")
                continue
        return podcasts

    def search_podcasts(self, search_query: str) -> dict[str, Any]:
        """
        Search for podcasts matching the search query and return parsed results.
        
        :param search_query: The search term for finding podcasts
        :type search_query: str
        
        :return: Dictionary with 'podcasts' key containing list of podcast dicts, or 'error' key with error message
        :rtype: Dict[str, Any]
        """
        url = self.base_url + search_query
        headers = self.generate_auth_headers()
        response = requests.post(url, headers=headers)

        if response.status_code == 200:
            search_results = json.loads(response.text)
            parsed_results = self.parse_search_results(search_results)
            # Convert Pydantic models to dicts for backward compatibility
            # Use model_dump with mode='json' to convert HttpUrl to strings
            return {'podcasts': [p.model_dump(mode='json') for p in parsed_results]}
        else:
            return {'error': f'Received {response.status_code}'}

# just a little test for freakonomics
if __name__ == '__main__':
    search = PodcastIndexSearch()
    results = search.fetch_podcasts("freakonomics")
    print(results)