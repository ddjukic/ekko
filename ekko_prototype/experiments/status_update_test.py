import streamlit as st
import requests
import threading
import time

def long_running_task(url, filename='yolov8x.pt'):
    # Send a GET request
    response = requests.get(url, stream=True)

    # Check if the request was successful
    if response.status_code == 200:
        print('downloading file')
        # Open the file in write mode
        with open(filename, 'wb') as file:
            # Write the contents of the response to the file
            for chunk in response.iter_content(chunk_size=1024):
                if chunk:
                    file.write(chunk)
    else:
        print(f"Failed to download file. Status code: {response.status_code}")

def update_progress(my_bar, duration):
    start_time = time.time()
    while time.time() - start_time < duration:
        time_elapsed = time.time() - start_time
        progress = time_elapsed / duration
        my_bar.progress(min(progress, 1.0))
        time.sleep(0.5)  # Update every 0.5 seconds
    my_bar.progress(1.0)  # Ensure progress is set to 100% at completion

url = "https://github.com/ultralytics/assets/releases/download/v8.2.0/yolov8x.pt"
estimated_duration = 10  # Estimate how long the request might take in seconds

progress_text = "Operation in progress. Please wait."

if st.button("Start long-running task"):
    # Start the long-running task in a background thread
    thread = threading.Thread(target=long_running_task, args=(url,))
    thread.start()
    # Update progress in the main thread
    my_bar = st.progress(0, text=progress_text)
    update_progress(my_bar, estimated_duration)
    thread.join()
    my_bar.empty()  # Optionally clear the progress bar

st.button("Rerun")
