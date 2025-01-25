import hashlib
import json
import requests
import time
from typing import List, Dict, Any, Optional
import os
import sys

# Add parent directory to path for imports
parent_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)

from config import config
from models import PodcastModel

class PodcastIndexSearch:
    """A class to interact with the PodcastIndex API to search for podcasts.

    Attributes:
        api_key (str): The API key for the PodcastIndex service.
        api_secret (str): The API secret for the PodcastIndex service.
    """
    def __init__(self, api_credentials_path: Optional[str] = None):
        """Initialize the PodcastIndexSearch class by loading the API credentials."""
        self.load_api_credentials(api_credentials_path)
        self.base_url = "https://api.podcastindex.org/api/1.0/search/byterm?q="

    def load_api_credentials(self, path: Optional[str] = None) -> Dict[str, str]:
        """Load the API key and secret from environment variables or JSON file.

        Args:
            path (str, optional): The path to the JSON file.

        Returns:
            dict: A dictionary containing the API key and secret.
        """
        # First try environment variables
        self.api_key = config.PODCASTINDEX_API_KEY
        self.api_secret = config.PODCASTINDEX_API_SECRET
        
        if self.api_key and self.api_secret:
            return {'success': 'API credentials loaded from environment.'}
        
        # Fallback to JSON file if provided
        if path:
            try:
                with open(path, 'r') as file:
                    credentials = json.load(file)
                    self.api_key = credentials.get('api_key', '')
                    self.api_secret = credentials.get('api_secret', '')
                    return {'success': 'API credentials loaded from file.'}
            except FileNotFoundError:
                return {'error': f'File not found: {path}'}
            except Exception as e:
                return {'error': str(e)}
        
        return {'error': 'No API credentials found'}

    def generate_auth_headers(self):
        """Generate the necessary authentication headers for the request."""
        epoch_time = int(time.time())
        data_to_hash = self.api_key + self.api_secret + str(epoch_time)
        sha_1 = hashlib.sha1(data_to_hash.encode()).hexdigest()

        return {
            'X-Auth-Date': str(epoch_time),
            'X-Auth-Key': self.api_key,
            'Authorization': sha_1,
            'User-Agent': 'postcasting-index-python-cli',
        }

    def parse_search_results(self, results: Dict[str, Any]) -> List[PodcastModel]:
        """Parse the search results to extract relevant podcast information.

        Args:
            results (dict): The search results to parse.

        Returns:
            list: A list of PodcastModel instances.
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

    def search_podcasts(self, search_query: str) -> Dict[str, Any]:
        """Search for podcasts matching the search query and return parsed results.

        Args:
            search_query (str): The podcast search query.

        Returns:
            dict: A dictionary containing the parsed podcast information or an error message.
        """
        url = self.base_url + search_query
        headers = self.generate_auth_headers()
        response = requests.post(url, headers=headers)

        if response.status_code == 200:
            search_results = json.loads(response.text)
            parsed_results = self.parse_search_results(search_results)
            # Convert Pydantic models to dicts for backward compatibility
            return {'podcasts': [p.dict() for p in parsed_results]}
        else:
            return {'error': f'Received {response.status_code}'}

# just a little test for freakonomics
if __name__ == '__main__':
    search = PodcastIndexSearch()
    results = search.fetch_podcasts("freakonomics")
    print(results)