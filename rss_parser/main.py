import argparse
import logging

import pandas as pd
import requests
from db_connection_manager import DatabaseConnectionManager
from episode_downloader import EpisodeDownloader
from feed_parser import DefaultFeedParserStrategy


# TODO: maybe move elsewhere
class FeedParserFactory:
    @staticmethod
    def get_parser(feed_url):
        # Logic to determine the appropriate parser based on the feed_url or its content
        # For now always returns the default parser (works for test feed)
        return DefaultFeedParserStrategy()


# Expanded CLI to accept a CSV file with feed URLs
def parse_arguments():
    parser = argparse.ArgumentParser(description="Podcast Downloader")
    parser.add_argument(
        "--feeds_csv", help="Location of the CSV file containing feed URLs"
    )
    parser.add_argument(
        "--look_back_days",
        type=int,
        default=7,
        help="Number of days to look back for episodes",
    )
    # Other arguments as needed
    return parser.parse_args()


# Function to parse the CSV file and return the list of feed URLs
def parse_csv(csv_file_path):
    logger = logging.getLogger(__name__)
    logger.info("Parsing CSV file")
    df = pd.read_csv(csv_file_path)

    feed_urls = df.RSS.tolist()
    feed_titles = df.Title.tolist()

    logger.info(f"Found {len(feed_urls)} feed URLs:")
    for title, url in zip(feed_titles, feed_urls, strict=False):
        logger.info(f"{title}: {url}")

    return feed_titles, feed_urls


def main():
    logger = logging.getLogger(__name__)
    db_manager = DatabaseConnectionManager()

    logging.basicConfig(level=logging.INFO)
    args = parse_arguments()
    feed_titles, feed_urls = parse_csv(args.feeds_csv)

    # temporarily remove the first feed
    feed_titles = feed_titles[1:]
    feed_urls = feed_urls[1:]

    for feed_title, feed_url in zip(feed_titles, feed_urls, strict=False):
        logger.info(f"Processing feed: {feed_url}")
        response = requests.get(feed_url)
        feed_content = response.content

        parser_strategy = FeedParserFactory.get_parser(feed_url)
        episodes = parser_strategy.parse(feed_content)

        downloader = EpisodeDownloader(feed_title, db_manager)
        downloader.download_episodes(episodes, args.look_back_days)


if __name__ == "__main__":
    main()
