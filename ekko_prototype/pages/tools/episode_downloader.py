import logging
import os

import requests


class EpisodeDownloader:
    """
    Handles downloading of podcast episodes.

    :ivar parent_folder: The parent directory for downloaded episodes
    :vartype parent_folder: str
    :ivar verbose: Flag to enable verbose logging
    :vartype verbose: bool
    """
    def __init__(self, parent_folder: str, verbose: bool = False):
        self.parent_folder = parent_folder
        self.logger = logging.getLogger(__name__)
        self.verbose = verbose

    def download_single_episode(self, url: str, title: str, feed_title: str) -> str | None:
        """
        Download a single episode with streaming and progress tracking.

        :param url: The URL of the episode's MP3 file
        :type url: str
        :param title: The title of the episode
        :type title: str
        :param feed_title: The title of the podcast feed
        :type feed_title: str

        :return: The full path of the downloaded episode or None if failed
        :rtype: Optional[str]

        .. note::
           Creates an MP3 file in the directory ./audio/feed_title/ named after the episode title.
        """
        # TODO;
        # resolve the issue of the episode title being not path friendly
        self.logger.debug(f"Starting download from: {url}")
        self.logger.debug(f"Episode title: {title}")
        episode_dir = self._create_episode_dir(feed_title)
        self.logger.debug(f"Episode dir: {episode_dir}")
        
        # Create safe filename
        safe_title = "".join([c for c in title if c.isalnum() or c in " -_"]).rstrip()[:100]
        safe_title = safe_title.replace(",", "").replace("/", "")
        file_path = os.path.join(episode_dir, f"{safe_title}.mp3")
        
        # Check if file already exists
        if os.path.exists(file_path):
            self.logger.info(f"Episode already downloaded: {file_path}")
            return file_path
        
        try:
            self.logger.info(f"Downloading episode: {title}")
            # Stream the download with timeout for initial connection
            response = requests.get(url, stream=True, timeout=30)
            response.raise_for_status()
            
            # Get file size if available
            total_size = int(response.headers.get('content-length', 0))
            if total_size > 0:
                self.logger.info(f"File size: {total_size / 1024 / 1024:.1f} MB")
            
            # Download in chunks
            chunk_size = 8192  # 8KB chunks
            downloaded = 0
            last_log = 0
            
            with open(file_path, 'wb') as file:
                for chunk in response.iter_content(chunk_size=chunk_size):
                    if chunk:
                        file.write(chunk)
                        downloaded += len(chunk)
                        
                        # Log progress every 5MB
                        if total_size > 0 and downloaded - last_log > 5 * 1024 * 1024:
                            progress = (downloaded / total_size) * 100
                            self.logger.info(f"Download progress: {progress:.1f}% ({downloaded / 1024 / 1024:.1f} MB / {total_size / 1024 / 1024:.1f} MB)")
                            last_log = downloaded
            
            self.logger.info(f"Successfully downloaded episode: {title}")
            return file_path
            
        except requests.exceptions.Timeout:
            self.logger.error(f"Download timeout for episode: {title}")
            # Clean up partial file
            if os.path.exists(file_path):
                os.remove(file_path)
            return None
        except requests.exceptions.RequestException as e:
            self.logger.error(f"Failed to download episode: {title}. Error: {e}")
            # Clean up partial file
            if os.path.exists(file_path):
                os.remove(file_path)
            return None
        except Exception as e:
            self.logger.error(f"Unexpected error downloading episode: {title}. Error: {e}")
            # Clean up partial file
            if os.path.exists(file_path):
                os.remove(file_path)
            return None

    def _create_episode_dir(self, feed_title: str) -> str:
        """
        Create a directory for a podcast feed.

        :param feed_title: Title of the podcast feed
        :type feed_title: str

        :return: The path to the created directory
        :rtype: str
        """
        safe_title = "".join([c for c in feed_title if c.isalnum() or c in " -_"]).rstrip()
        episode_dir = os.path.join(self.parent_folder, safe_title)
        os.makedirs(episode_dir, exist_ok=True)
        return episode_dir