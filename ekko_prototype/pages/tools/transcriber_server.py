import logging

import uvicorn
from episode_downloader import EpisodeDownloader
from fastapi import Depends, FastAPI, HTTPException
from fastapi.security import HTTPBearer
from pydantic import BaseModel
from pyngrok import ngrok

from audio_transcriber import EpisodeTranscriber

# TODO:
# figure out why logging isnt flushed to a file
# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    filename="transcriber_server_logs.log",
    filemode="a",
)
console_handler = logging.StreamHandler()
console_handler.setLevel(logging.INFO)
formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
console_handler.setFormatter(formatter)
logging.getLogger().addHandler(console_handler)

app = FastAPI()
security = HTTPBearer()


class TranscriptionRequest(BaseModel):
    episode_url: str
    episode_title: str
    podcast_title: str


def verify_token(credentials: HTTPBearer = Depends(security)):
    """Verify the given token with the expected token.

    :param credentials: Security credentials from the request
    :type credentials: HTTPBearer
    :raises HTTPException: If the token is invalid
    :return: The verified token
    :rtype: str
    """
    correct_token = (
        "chamberOfSecrets"  # TODO: handle token creation and validation better
    )
    if credentials.credentials != correct_token:
        raise HTTPException(status_code=403, detail="Invalid authentication token")
    return credentials.credentials


@app.post("/transcribe")
async def transcribe_audio(
    request: TranscriptionRequest, token: str = Depends(verify_token)
):
    """Process transcription request by downloading, transcribing, and uploading the audio file.

    :param request: Transcription request details including the URL, title, and podcast name
    :type request: TranscriptionRequest
    :param token: Authentication token, defaults to a token provided by security dependency
    :type token: str, optional
    :return: Path where the transcription file is stored
    :rtype: dict
    """

    # Log the request payload
    logging.info(f"Received request to transcribe audio: {request.model_dump_json()}")
    local_file_path = downloader.download_single_episode(
        request.episode_url, request.episode_title, request.podcast_title
    )
    logging.info(f"Downloaded audio file to: {local_file_path}")
    transcription_path = transcriber.transcribe(local_file_path)
    logging.info(f"Transcribed audio to: {transcription_path}")
    upload_path = transcriber.upload(transcription_path)
    logging.info(f"Uploaded transcription to: {upload_path}")
    return {"transcription_file_path": upload_path}


if __name__ == "__main__":
    # Tunnel the FastAPI server on port 8000
    downloader = EpisodeDownloader("./audio")
    transcriber = EpisodeTranscriber()
    public_url = ngrok.connect(8000, name="transcriber_server")
    # TODO:
    # upload the url into a config in lightning studio so it gets automatically picked up
    print(f"Public URL: {public_url}")
    uvicorn.run(app, host="0.0.0.0", port=8000)
