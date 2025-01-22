import logging
from datetime import datetime, timedelta
import requests
import os
from db_connection_manager import DatabaseConnectionManager

class EpisodeDownloader:
    """Handles downloading of podcast episodes."""
    def __init__(self, parent_folder: str, db_manager: DatabaseConnectionManager, verbose: bool = False):
        self.parent_folder = parent_folder
        self.db_manager = db_manager
        self.logger = logging.getLogger(__name__)
        self.verbose = verbose

    def download_episodes(self, episodes, look_back_days):
        look_back_date = datetime.now() - timedelta(days=look_back_days)
        for episode in episodes:
            if episode.publication_date >= look_back_date:
                if not self.db_manager.episode_downloaded(episode.mp3_url):
                    self._download_episode(episode)
                    self.db_manager.add_episode(self.parent_folder, episode)
                else:
                    if self.verbose:
                        self.logger.info(f"Episode not downloaded: {episode.title}; in the database or too old.")

    def _download_episode(self, episode):
        response = requests.get(episode.mp3_url)
        episode_dir = self._create_episode_dir(episode.title)
        with open(os.path.join(episode_dir, f"{episode.title}.mp3"), 'wb') as file:
            file.write(response.content)

    def _create_episode_dir(self, episode_title):
        safe_title = "".join([c for c in episode_title if c.isalnum() or c in " -_"]).rstrip()
        episode_dir = os.path.join(self.parent_folder, safe_title)
        os.makedirs(episode_dir, exist_ok=True)
        return episode_dir