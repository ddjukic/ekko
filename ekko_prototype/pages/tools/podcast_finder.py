import hashlib
import json
import requests
import time

class PodcastIndexSearch:
    """A class to interact with the PodcastIndex API to search for podcasts.

    Attributes:
        api_key (str): The API key for the PodcastIndex service.
        api_secret (str): The API secret for the PodcastIndex service.
    """
    def __init__(self, api_credentials_path='api_credentials.json'):
        """Initialize the PodcastIndexSearch class by loading the API credentials."""
        self.load_api_credentials(api_credentials_path)
        self.base_url = "https://api.podcastindex.org/api/1.0/search/byterm?q="

    def load_api_credentials(self, path):
        """Load the API key and secret from a JSON file.

        Args:
            path (str, optional): The path to the JSON file. Defaults to 'api_credentials.json'.

        Returns:
            dict: A dictionary containing the API key and secret.
        """
        try:
            with open(path, 'r') as file:
                credentials = json.load(file)
                self.api_key = credentials['api_key']
                self.api_secret = credentials['api_secret']
                return {'success': 'API credentials loaded successfully.'}
        except FileNotFoundError:
            return {'error': f'File not found: {path}'}
        except Exception as e:
            return {'error': str(e)}

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

    def parse_search_results(self, results):
        """Parse the search results to extract relevant podcast information.

        Args:
            results (dict): The search results to parse.

        Returns:
            list: A list of dictionaries, each containing the title, url, and image of a podcast.
        """
        podcasts = []
        for feed in results.get('feeds', []):
            podcasts.append({
                'title': feed.get('title', ''),
                'url': feed.get('url', ''),
                'image': feed.get('image', '')
            })
        return podcasts

    def search_podcasts(self, search_query):
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
            return {'podcasts': parsed_results}
        else:
            return {'error': f'Received {response.status_code}'}

# just a little test for freakonomics
if __name__ == '__main__':
    search = PodcastIndexSearch()
    results = search.fetch_podcasts("freakonomics")
    print(results)