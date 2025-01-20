import logging
import os
import requests

class EpisodeDownloader:
    """Handles downloading of podcast episodes.

    Attributes:
        parent_folder (str): The parent directory for downloaded episodes.
        verbose (bool): Flag to enable verbose logging.
    """
    def __init__(self, parent_folder: str, verbose: bool = False):
        self.parent_folder = parent_folder
        self.logger = logging.getLogger(__name__)
        self.verbose = verbose

    def download_single_episode(self, url, title, feed_title):
        """Download a single episode.

        Args:
            url (str): The URL of the episode's MP3 file.
            title (str): The title of the episode.
            feed_title (str): The title of the podcast feed.

        Returns:
            str: The full path of the downloaded episode.

        Creates an MP3 file in the directory ./audio/feed_title/ named after the episode title.
        """
        # TODO;
        # resolve the issue of the episode title being not path friendly
        episode_dir = self._create_episode_dir(feed_title)
        response = requests.get(url)
        safe_title = "".join([c for c in feed_title if c.isalnum() or c in " -_"]).rstrip()
        safe_title = safe_title.replace(",", "").replace("/", "")
        file_path = os.path.join(episode_dir, f"{safe_title}.mp3")
        if response.ok:
            with open(file_path, 'wb') as file:
                file.write(response.content)
                if self.verbose:
                    self.logger.info(f"Downloaded episode: {title}")
            return file_path
        else:
            if self.verbose:
                self.logger.error(f"Failed to download episode: {title}")
            return None

    def _create_episode_dir(self, feed_title):
        """Create a directory for a podcast feed.

        Args:
            feed_title (str): The title of the podcast feed.

        Returns:
            str: The path to the created directory.
        """
        safe_title = "".join([c for c in feed_title if c.isalnum() or c in " -_"]).rstrip()
        episode_dir = os.path.join(self.parent_folder, safe_title)
        os.makedirs(episode_dir, exist_ok=True)
        return episode_dir