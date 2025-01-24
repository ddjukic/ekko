# Usage
import streamlit as st
import requests

def consume_stream(url, token):
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.get(url, headers=headers, stream=True)
    
    for line in response.iter_lines():

        if line:
            yield line.decode("utf-8")

# Set up the Streamlit app
st.title('Streaming Data Viewer')

# Start streaming
url = "https://5950-83-64-146-146.ngrok-free.app/stream"  # Replace this with your actual ngrok URL
token = "test_token"  # Replace this with your actual token

if st.button('Consume stream'):

    with st.spinner('Streaming content:'):
        st.write_stream(consume_stream(url, token))
    st.success('Request completed')