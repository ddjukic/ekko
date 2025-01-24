import streamlit as st
import requests
import os
import sys
import glob
import time
import readtime

ekko_icon = glob.glob('./**/ekko.png', recursive=True)[0]
st.set_page_config(page_title='ekko v0.1', page_icon=ekko_icon)

# Fix import paths for tools module
from ekko_prototype.pages.tools.podcast_finder import PodcastIndexSearch
from ekko_prototype.pages.tools.feed_parser import FeedParser
from ekko_prototype.pages.tools.summary_creator import TranscriptSummarizer
from ekko_prototype.pages.tools.podcast_chatbot import ChatBotInterface
# from ekko_prototype.pages.tools.audio_transcriber import calculate_ratio, estimate_processing_time
from ekko_prototype.pages.tools.retry import retry

# TODO:
# improve token security handling
TOKEN = 'chamberOfSecrets'
URL = 'https://internally-next-serval.ngrok-free.app'

# use glob for actually finding the file because of
# weird bugs in the lightning.ai filesystem apparently
# also retry because apparently there is a bit of a 
# filesystem latency
@retry(num_retries=10, sleep_between=1.5)
def find_file(filename):
    # sleep for a moment to give the file system to refresh
    time.sleep(1)
    return glob.glob(f'./**/{filename}', recursive=True)

# TODO:
# improve the docstrings; handle the TOKEN properly
def transcribe_episode_request(episode, feed_title):
    """
    Transcribes an episode and returns the transcription file path."""
    
    headers = {"Authorization": f"Bearer {TOKEN}"}

    # Make HTTP request to ngrok server
    url = f"{URL}/transcribe"
    data = {
        "episode_url": episode.mp3_url,
        "episode_title": episode.title,
        "podcast_title": feed_title
    }
    response = requests.post(url, headers=headers, json=data)

    # Check if request was successful
    if response.status_code == 200:
        # Unpack the 'transcription_file_path' from the response
        transcription_file_path = response.json().get("transcription_file_path")
        return transcription_file_path
    else:
        # Handle request error
        st.error(f"Failed to transcribe episode; server unreachable.")
        print(f'response status code: {response.status_code}')
        return None

# TODO:
# docstring
def summarize_episode(episode_transcript):

    # Read the transcription file
    with open(episode_transcript, "r") as file:
        transcription_text = file.read()

    # Create the summary
    summarizer = TranscriptSummarizer(system_file_path='./ekko/ekko_prototype/pages/tools/prompts/extract_wisdom_updated.md')
    # write the summary stream
    summary = st.write_stream(summarizer.summarize_transcript(transcription_text))

    st.write(f'Estimated reading time: {str(readtime.of_text(summary).text)}')
    # st.write("Please provide feedback:")
    # Provide feedback on the summary
    # feedback = streamlit_feedback(
    #     feedback_type="faces",
    #     optional_text_label="[Optional] Please provide feedback on the summary:",
    # )

def mock(func):
    st.write(f'would perform {func.__name__}')
    time.sleep(1)
    return True

def _re_search():
    # resets the currently selected podcast
    st.session_state.pop('selected_podcast', None)

def parse_time(time_string):
    """
    Parses a time string in the format 'HH:MM:SS' and returns the total number of seconds.
    """
    parsed = list(map(int, time_string.split(':')))
    if len(parsed) == 2:
        minutes, seconds = parsed
        hours = 0
    else:
        hours, minutes, seconds = parsed
    # return hours * 3600 + minutes * 60 + seconds
    return (hours, minutes, seconds)
    

# new feature that tells only the chat to reload, the rest stays
@st.experimental_fragment
def chat_with_podcast(episode_transcript, episode_title):
    
    if not os.path.exists(episode_transcript):
        st.error("Episode transcript not found.")
        return

    with st.spinner('Loading the chatbot...'):
        # Load the chatbot interface
        chatbot = ChatBotInterface(
            transcript_path=episode_transcript
        )

    chatbot.chat(episode_title)

def display_episodes(episodes, num_episodes, feed_title):
    """
    Displays a specified number of episodes as expandable elements with details and a 'Summarize episode' button.

    Args:
        episodes (list): A list of episode objects containing title, publication_date, and mp3_url.
        num_episodes (int): The number of episodes to display.
    """
    for episode in episodes[:num_episodes]:  # Only display up to num_episodes episodes
        episode_title = episode.title.strip()
        with st.expander(f":orange[**{episode_title}**] \n"):
            # Using Markdown to style the episode title and details
            # The h4 title is redundant; but see how to format the expander title like this
            # st.markdown(f"<h4 style='color: #f9e79f;'>{episode.title.strip()}</h4>", unsafe_allow_html=True)
            st.markdown(f"**Published on:** {episode.publication_date}\n- Duration: {episode.duration}")

            button_key = f"summarize_{episode.title}"
            try:
                if st.button(f"Summarize episode", key=button_key):

                    try:
                        h,m,s = parse_time(episode.duration)
                    except Exception as e:
                        print(e)
                        print(f'unknowns time string format, {episode.duration}')

                    # # The server-based download/transcribe flow
                    # TODO:
                    # provide a status update estimated based on the length of the episode
                    with st.spinner('Transcribing episode...'):
                        # st.write(f'Estimated processing time: {estimate_processing_time(h, m, s, ratio)}')
                        st.write('Estimated processing time: ~1 minute')

                        # transcription_file_path = transcribe_episode_request(episode, feed_title)
                        transcription_file_path = simulate_transcription()
                        if not transcription_file_path:
                            st.error("Failed to transcribe episode.")
                            return

                        file_basename = os.path.basename(transcription_file_path)

                        with st.spinner('Uploading the transcript...'):
                            try:
                                transcription_file_path = find_file(file_basename)[0]
                            except Exception as e:
                                st.error("Upload failed; please try clicking the 'Summarize episode' button again.")
                        
                        file_transcribed = os.path.exists(transcription_file_path)
                        if file_transcribed:
                            st.success(f"Transcription completed!")
                        else:
                            st.error(f"Transcription file not found at {transcription_file_path}; please try clicking the 'Summarize episode' again")
                            return
                    
                    # summarize
                    with st.spinner('Summarizing episode...'):
                        try:
                            summarize_episode(transcription_file_path)  
                        except Exception as e:
                            st.write(f'Summarization failed; {e}')
                    
                    # chat
                    try:
                        chat_with_podcast(transcription_file_path, episode_title=episode_title)
                    except Exception as e:
                        st.error(f"Failed to load chatbot: {e}")

                    # provide feedback
                    st.session_state['feedback_round'] = 'prototype_evaluation'
                    st.session_state['question_counter'] = 0
                    # st.page_link('./pages/feedback_record.py', label="Click to provide feedback 🥰")
                    st.link_button('Click to provide feedback 🥰', 'https://forms.gle/CQeBVQj8B52RpF1P8')

            # TODO:
            # see how to handle the duplicate episodes better
            except:
                print('duplicate episode, skipping')

def search_podcast():

    st.header("Search for a Podcast")
    podcast_name = st.text_input("Enter the name of the podcast:", on_change=_re_search)
            
    if podcast_name:

        # Use absolute path or relative from current file location
        import os
        creds_path = os.path.join(os.path.dirname(__file__), 'creds', 'api_credentials.json')
        search = PodcastIndexSearch(creds_path)
        results = search.search_podcasts(podcast_name)
        
        if results and 'podcasts' in results and len(results['podcasts']) > 0:
            
            if 'selected_podcast' not in st.session_state:
                st.subheader("Top 5 search results:")
                for i, podcast in enumerate(results['podcasts'][:5]):
                    feed_title = podcast['title']
                    with st.expander(f"{feed_title}"):
                        st.image(podcast['image'], caption=podcast['title'], width=250)
                        if st.button("Select", key=f'selected_podcast_{feed_title}_{i}'):
                            st.session_state['selected_podcast'] = podcast
                            st.rerun()

            else:
                podcast = st.session_state.selected_podcast
                st.image(podcast['image'], caption=podcast['title'], width=290)
                feed_title = podcast['title']
                st.subheader(f"Episodes of {feed_title}")
            
                # Pass the RSS feed URL to the feed parser
                feed_url = podcast['url']
                feed_parser = FeedParser()
                episodes = feed_parser.parse_feed(feed_url)
                print(feed_url)
                
                # Allow users to select the number of episodes to display
                num_episodes = st.selectbox("Select the number of past episodes to display:", (20, 50, 100, 200), index=0)
                
                # Display episodes
                st.subheader("Episodes:")
                display_episodes(episodes, num_episodes, feed_title)

# TODO:
# define the prompt inside the patterns with the user context 
def update_context():
    pass

def main():

    # transcription ratio
    audio_lengths_minutes = [13.776983333333334, 10.85]
    processing_times_seconds = [8.37, 6.39]
    
    # TODO:
    # think about where to place this
    global ratio
    # ratio = calculate_ratio(audio_lengths_minutes, processing_times_seconds)

    st.title("Ekko Prototype v0.1")
    search_podcast()

def simulate_transcription():
    """Simulates the transcription process by sleeping for 1 second and returning the demo transcript path."""
    time.sleep(1)
    demo_transcript_path = "/home/dd/dejan_dev/ekko/audio_transcriber/demo.txt"
    # local_transcript_path = "./transcripts/demo.txt"
    # shutil.copy(demo_transcript_path, local_transcript_path)
    return demo_transcript_path

if __name__ == "__main__":
    main()
