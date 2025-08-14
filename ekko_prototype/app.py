import glob
import os
import sys
import time
from typing import Any

import readtime
import requests
import streamlit as st

# Fix import paths for tools module
# Add parent dir to path for imports when running from app.py directly
parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)

from ekko_prototype.auth import auth
from ekko_prototype.logging_config import get_logger, setup_streamlit_logging
from ekko_prototype.models import EpisodeModel as Episode
from ekko_prototype.models import TranscriptConfig
from ekko_prototype.pages.tools.feed_parser import FeedParser
from ekko_prototype.pages.tools.podcast_chatbot import ChatBotInterface
from ekko_prototype.pages.tools.podcast_finder import PodcastIndexSearch
from ekko_prototype.pages.tools.retry import retry
from ekko_prototype.pages.tools.summary_creator import TranscriptSummarizer
from ekko_prototype.pages.tools.transcript_fetcher import UnifiedTranscriptFetcher

# Set up logging
setup_streamlit_logging()
logger = get_logger(__name__)

ekko_icon = glob.glob("./**/ekko.png", recursive=True)[0]
st.set_page_config(page_title="ekko v0.1", page_icon=ekko_icon)

# TODO:
# improve token security handling
TOKEN = "chamberOfSecrets"
URL = "https://internally-next-serval.ngrok-free.app"


# use glob for actually finding the file because of
# weird bugs in the lightning.ai filesystem apparently
# also retry because apparently there is a bit of a
# filesystem latency
@retry(num_retries=10, sleep_between=1.5)
def find_file(filename: str) -> list[str]:
    # sleep for a moment to give the file system to refresh
    time.sleep(1)
    return glob.glob(f"./**/{filename}", recursive=True)


# TODO:
# improve the docstrings; handle the TOKEN properly
def transcribe_episode_request(episode: Episode, feed_title: str) -> str | None:
    """
    Transcribes an episode and returns the transcription file path.

    :param episode: Episode object to transcribe
    :type episode: Episode
    :param feed_title: Title of the podcast feed
    :type feed_title: str

    :return: Path to transcription file if successful, None otherwise
    :rtype: Optional[str]
    """
    headers = {"Authorization": f"Bearer {TOKEN}"}

    # Make HTTP request to ngrok server
    url = f"{URL}/transcribe"
    data = {
        "episode_url": episode.audio_url,
        "episode_title": episode.title,
        "podcast_title": feed_title,
    }
    response = requests.post(url, headers=headers, json=data)

    # Check if request was successful
    if response.status_code == 200:
        # Unpack the 'transcription_file_path' from the response
        transcription_file_path = response.json().get("transcription_file_path")
        return transcription_file_path
    else:
        # Handle request error
        st.error("Failed to transcribe episode; server unreachable.")
        print(f"response status code: {response.status_code}")
        return None


# TODO:
# docstring
def summarize_episode(episode_transcript: str) -> None:
    """
    Summarize an episode transcript using GPT-4.

    :param episode_transcript: Path to transcript file
    :type episode_transcript: str
    """
    # Read the transcription file
    with open(episode_transcript) as file:
        transcription_text = file.read()

    # Create the summary
    import os

    prompt_path = os.path.join(
        os.path.dirname(__file__),
        "pages",
        "tools",
        "prompts",
        "extract_wisdom_updated.md",
    )
    # Only use credentials file if it exists, otherwise rely on environment variables
    creds_path = os.path.join(
        os.path.dirname(__file__), "creds", "openai_credentials.json"
    )
    if not os.path.exists(creds_path):
        creds_path = None

    summarizer = TranscriptSummarizer(
        system_file_path=prompt_path, credentials_file_path=creds_path
    )
    # write the summary stream
    summary = st.write_stream(summarizer.summarize_transcript(transcription_text))

    st.write(f"Estimated reading time: {readtime.of_text(summary).text!s}")
    # st.write("Please provide feedback:")
    # Provide feedback on the summary
    # feedback = streamlit_feedback(
    #     feedback_type="faces",
    #     optional_text_label="[Optional] Please provide feedback on the summary:",
    # )


def mock(func: Any) -> bool:
    st.write(f"would perform {func.__name__}")
    time.sleep(1)
    return True


def _re_search() -> None:
    # resets the currently selected podcast
    st.session_state.pop("selected_podcast", None)


def parse_time(time_string: str) -> tuple[int, int, int]:
    """
    Parses a time string in the format 'HH:MM:SS' and returns the hours, minutes, and seconds.

    :param time_string: Time string in format 'HH:MM:SS' or 'MM:SS'
    :type time_string: str

    :return: Tuple of (hours, minutes, seconds)
    :rtype: Tuple[int, int, int]
    """
    parsed = list(map(int, time_string.split(":")))
    if len(parsed) == 2:
        minutes, seconds = parsed
        hours = 0
    else:
        hours, minutes, seconds = parsed
    # return hours * 3600 + minutes * 60 + seconds
    return (hours, minutes, seconds)


# new feature that tells only the chat to reload, the rest stays
@st.fragment
def chat_with_podcast(episode_transcript: str, episode_title: str) -> None:
    """
    Create an interactive chat interface for a podcast episode.

    :param episode_transcript: Path to transcript file
    :type episode_transcript: str
    :param episode_title: Title of the episode
    :type episode_title: str
    """

    if not os.path.exists(episode_transcript):
        st.error("Episode transcript not found.")
        return

    with st.spinner("Loading the chatbot..."):
        # Load the chatbot interface
        # Only use credentials file if it exists, otherwise rely on environment variables
        creds_path = os.path.join(
            os.path.dirname(__file__), "creds", "openai_credentials.json"
        )
        if not os.path.exists(creds_path):
            creds_path = None

        chatbot = ChatBotInterface(
            transcript_path=episode_transcript, credentials_path=creds_path
        )

    chatbot.chat(episode_title)


def display_episodes(
    episodes: list[Episode],
    num_episodes: int,
    feed_title: str,
    feed_url: str | None = None,
) -> None:
    """
    Displays a specified number of episodes as expandable elements with details and a 'Summarize episode' button.

    :param episodes: A list of episode objects containing title, published_date, and audio_url
    :type episodes: List[Episode]
    :param num_episodes: The number of episodes to display
    :type num_episodes: int
    :param feed_title: The title of the podcast feed
    :type feed_title: str
    :param feed_url: The RSS feed URL of the podcast
    :type feed_url: Optional[str]
    """
    for episode in episodes[:num_episodes]:  # Only display up to num_episodes episodes
        episode_title = episode.title.strip()
        with st.expander(f":orange[**{episode_title}**] \n"):
            # Using Markdown to style the episode title and details
            # The h4 title is redundant; but see how to format the expander title like this
            # st.markdown(f"<h4 style='color: #f9e79f;'>{episode.title.strip()}</h4>", unsafe_allow_html=True)
            st.markdown(
                f"**Published on:** {episode.published_date}\n- Duration: {episode.duration}"
            )

            button_key = f"summarize_{episode.title}"
            try:
                if st.button("Summarize episode", key=button_key):
                    # Check rate limit before proceeding
                    if not auth.can_transcribe():
                        continue

                    try:
                        h, m, s = parse_time(episode.duration)
                    except Exception as e:
                        print(e)
                        print(f"unknowns time string format, {episode.duration}")

                    # Use intelligent transcript fetching
                    st.info(
                        "Fetching transcript (checking YouTube first, then Whisper)..."
                    )

                    # Initialize the unified transcript fetcher
                    transcript_config = TranscriptConfig(
                        prefer_youtube=True,
                        use_openai_whisper=True,  # Use OpenAI Whisper API
                        use_remote_whisper=False,
                        cache_transcripts=True,
                    )
                    fetcher = UnifiedTranscriptFetcher(transcript_config)

                    try:
                        logger.info(f"Starting transcript fetch for: {episode_title}")
                        # Get the transcript
                        result = fetcher.get_transcript(
                            podcast_name=feed_title,
                            episode_title=episode_title,
                            episode_audio_url=episode.audio_url,
                            podcast_rss_url=feed_url,
                        )

                        if not result or not result.text:
                            st.error("Failed to fetch transcript. Please try again.")
                            logger.error(f"Transcript fetch failed - result: {result}")
                            if result:
                                logger.error(
                                    f"Source: {result.source}, metadata: {result.metadata}"
                                )
                            continue  # Skip to next episode
                    except Exception as e:
                        st.error(f"Error fetching transcript: {e!s}")
                        logger.exception("Error during transcript fetching")
                        import traceback

                        st.code(traceback.format_exc())
                        continue  # Skip to next episode

                    # Save transcript to a temporary file
                    import tempfile

                    os.makedirs("./transcripts", exist_ok=True)
                    with tempfile.NamedTemporaryFile(
                        mode="w", suffix=".txt", delete=False, dir="./transcripts"
                    ) as f:
                        f.write(result.text)
                        transcription_file_path = f.name

                    # Show source of transcript
                    st.success(f"Transcript obtained from: {result.source.value}")
                    if result.metadata.get("youtube_url"):
                        st.info(f"YouTube URL: {result.metadata['youtube_url']}")

                    # Increment usage counter
                    auth.increment_usage()
                    within_limit, remaining = auth.check_rate_limit()
                    if remaining > 0:
                        st.info(
                            f"You have {remaining} transcript{'s' if remaining != 1 else ''} remaining today."
                        )
                    else:
                        st.warning("You've used your daily limit of transcripts!")

                    # summarize
                    with st.spinner("Summarizing episode..."):
                        try:
                            summarize_episode(transcription_file_path)
                        except Exception as e:
                            st.write(f"Summarization failed; {e}")

                    # chat
                    try:
                        chat_with_podcast(
                            transcription_file_path, episode_title=episode_title
                        )
                    except Exception as e:
                        st.error(f"Failed to load chatbot: {e}")

                    # provide feedback
                    st.session_state["feedback_round"] = "prototype_evaluation"
                    st.session_state["question_counter"] = 0
                    # st.page_link('./pages/feedback_record.py', label="Click to provide feedback 🥰")
                    st.link_button(
                        "Click to provide feedback 🥰",
                        "https://forms.gle/CQeBVQj8B52RpF1P8",
                    )

            # TODO:
            # see how to handle the duplicate episodes better
            except:
                print("duplicate episode, skipping")


def search_podcast() -> None:
    """
    Main podcast search and display interface.
    """

    st.header("🔍 Search for a Podcast")
    podcast_name = st.text_input(
        "Enter the name of the podcast:",
        on_change=_re_search,
        placeholder="e.g., Lenny's Podcast, The Daily",
    )

    if podcast_name:
        # Use absolute path or relative from current file location
        import os

        # Only use credentials file if it exists, otherwise rely on environment variables
        creds_path = os.path.join(
            os.path.dirname(__file__), "creds", "api_credentials.json"
        )
        if not os.path.exists(creds_path):
            creds_path = None

        search = PodcastIndexSearch(creds_path)
        results = search.search_podcasts(podcast_name)

        if results and "podcasts" in results and len(results["podcasts"]) > 0:
            if "selected_podcast" not in st.session_state:
                st.subheader("Top 5 search results:")
                for i, podcast in enumerate(results["podcasts"][:5]):
                    feed_title = podcast["title"]
                    with st.expander(f"{feed_title}"):
                        st.image(podcast["image"], caption=podcast["title"], width=250)
                        if st.button(
                            "Select", key=f"selected_podcast_{feed_title}_{i}"
                        ):
                            st.session_state["selected_podcast"] = podcast
                            st.rerun()

            else:
                podcast = st.session_state.selected_podcast
                st.image(podcast["image"], caption=podcast["title"], width=290)
                feed_title = podcast["title"]
                st.subheader(f"Episodes of {feed_title}")

                # Pass the RSS feed URL to the feed parser
                feed_url = podcast["url"]
                feed_parser = FeedParser()
                episodes = feed_parser.parse_feed(feed_url)
                logger.debug(f"Parsing feed: {feed_url}")

                # Allow users to select the number of episodes to display
                num_episodes = st.selectbox(
                    "Select the number of past episodes to display:",
                    (20, 50, 100, 200),
                    index=0,
                )

                # Display episodes
                st.subheader("Episodes:")
                display_episodes(episodes, num_episodes, feed_title, feed_url)


# TODO:
# define the prompt inside the patterns with the user context
def update_context() -> None:
    """Update user context for personalization."""
    pass


def main() -> None:
    """
    Main application entry point.
    """

    # transcription ratio

    # TODO:
    # think about where to place this
    global ratio
    # ratio = calculate_ratio(audio_lengths_minutes, processing_times_seconds)

    st.title("🎙️ ekko - AI Podcast Discovery & Summarization")

    # Show authentication form if not authenticated
    if not auth.require_auth():
        st.info(
            "Sign in with your email to start discovering and summarizing podcasts!"
        )
        return

    # Show usage info in sidebar
    auth.display_usage_info()

    # Main app functionality
    search_podcast()


def simulate_transcription() -> str:
    """Simulates the transcription process by sleeping for 1 second and returning the demo transcript path.

    :return: Path to demo transcript file
    :rtype: str
    """
    time.sleep(1)
    demo_transcript_path = "/home/dd/dejan_dev/ekko/audio_transcriber/demo.txt"
    # local_transcript_path = "./transcripts/demo.txt"
    # shutil.copy(demo_transcript_path, local_transcript_path)
    return demo_transcript_path


if __name__ == "__main__":
    main()
