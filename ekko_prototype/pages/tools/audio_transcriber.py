import argparse
import torch
from transformers import AutoModelForSpeechSeq2Seq, AutoProcessor, pipeline
from transformers.utils import is_flash_attn_2_available
import os
import time
from pydub import AudioSegment
from lightning_sdk import Studio

def calculate_ratio(audio_lengths_minutes, processing_times_seconds):
    """
    Calculates the average ratio of processing time to audio length for a list of audio files.

    :param audio_lengths_minutes: List of lengths of the audio files in minutes.
    :type audio_lengths_minutes: list[float]
    :param processing_times_seconds: List of times taken to process the audio files in seconds.
    :type processing_times_seconds: list[float]
    :return: Average ratio of processing time per second of audio.
    :rtype: float
    """
    assert len(audio_lengths_minutes) == len(processing_times_seconds), "Lists must be of equal length"
    total_ratio = 0
    for audio_length, processing_time in zip(audio_lengths_minutes, processing_times_seconds):
        audio_length_seconds = audio_length * 60  # Convert minutes to seconds
        ratio = processing_time / audio_length_seconds
        total_ratio += ratio
    average_ratio = total_ratio / len(audio_lengths_minutes)
    return average_ratio

def estimate_processing_time(audio_length_hours, audio_length_minutes, audio_length_seconds, ratio):
    """
    Estimates the processing time based on the audio length and a given ratio, and returns the time in minutes and seconds if more than 60 seconds.
    
    :param audio_length_hours: Hours of the audio length
    :type audio_length_hours: int
    :param audio_length_minutes: Minutes of the audio length
    :type audio_length_minutes: int
    :param audio_length_seconds: Seconds of the audio length
    :type audio_length_seconds: int
    :param ratio: Calculated ratio of processing time per second of audio
    :type ratio: float
    :return: Estimated processing time formatted as a string indicating minutes and seconds if more than 60 seconds, otherwise just seconds
    :rtype: str
    """
    total_audio_seconds = audio_length_hours * 3600 + audio_length_minutes * 60 + audio_length_seconds
    estimated_processing_seconds = total_audio_seconds * ratio

    if estimated_processing_seconds <= 60:
        return f"{estimated_processing_seconds:.2f} seconds"
    else:
        minutes = int(estimated_processing_seconds // 60)
        seconds = estimated_processing_seconds % 60
        return f"{minutes} minutes and {seconds:.2f} seconds"
    
class EpisodeTranscriber:
    """Transcribes podcast episodes from MP3 files."""

    def __init__(self, parent_folder="./transcripts", model_id="distil-whisper/distil-large-v3"):
        """
        Initialize the transcriber with the appropriate model and device settings.

        :param parent_folder: The directory where the transcriptions will be saved.
        :param model_id: The model ID for the transcription model.
        """
        self.parent_folder = parent_folder
        os.makedirs(self.parent_folder, exist_ok=True)
        self.setup_device_and_model(model_id)

    def setup_device_and_model(self, model_id):
        """
        Sets up device and model based on availability of GPU and Flash Attention 2.

        :param model_id: The model ID for the transcription model.
        """
        if is_flash_attn_2_available() and torch.cuda.is_available():
            print("Using Flash Attention 2 and GPU")
            device = "cuda:0"
            torch_dtype = torch.float16
        else:
            print("Using CPU execution")
            torch_dtype = torch.float32
            device = "cpu"

        self.device = device
        self.torch_dtype = torch_dtype

        self.model = AutoModelForSpeechSeq2Seq.from_pretrained(
            model_id, torch_dtype=self.torch_dtype, low_cpu_mem_usage=True, use_safetensors=True,
            attn_implementation="flash_attention_2"
        ).to(self.device)

        self.processor = AutoProcessor.from_pretrained(model_id)

        self.pipe = pipeline(
            "automatic-speech-recognition",
            model=self.model,
            tokenizer=self.processor.tokenizer,
            feature_extractor=self.processor.feature_extractor,
            max_new_tokens=128,
            chunk_length_s=25,
            batch_size=16,
            torch_dtype=self.torch_dtype,
            device=self.device,
        )

    def transcribe(self, mp3_file):
        """
        Transcribe the given MP3 file.

        :param mp3_file: Path to the MP3 file to transcribe.
        :returns: Path to the transcription text file.
        """
        audio = AudioSegment.from_mp3(mp3_file)
        audio_length = len(audio) / 60000  # Convert milliseconds to minutes
        start_time = time.time()
        outputs = self.pipe(mp3_file)
        transcription_time = time.time() - start_time
        print(f"{audio_length} mins of audio transcribed in {transcription_time:.2f} seconds.")
        return self.save(outputs, mp3_file)

    def save(self, outputs, mp3_file):
        """
        Save transcription to a text file.

        :param outputs: Transcription text from the model.
        :param mp3_file: Path to the MP3 file transcribed.
        :returns: Path to the saved text file.
        """
        title = os.path.basename(mp3_file).split('.')[0]
        output_file = os.path.join(self.parent_folder, f"{title}.txt")
        with open(output_file, 'w', encoding='utf-8') as file:
            file.write(outputs['text'])
        return output_file

    def upload(self, file_path):
        """
        Uploads a file to a remote server.

        :param file_path: Local path to the file to upload.
        :returns: Remote path of the uploaded file.
        """
        studio = Studio(name='fixed-moccasin-3jhs', teamspace='ekko', user='dejandukic')
        # its a little confusing; but the path for the file on the remote server is somehow
        # automatically made relative to the teamspace, i suppose; thats why the dot works
        remote_path = f"/teamspace/studios/this_studio/ekko/ekko_prototype/transcripts/{os.path.basename(file_path)}"
        print('Destination:', remote_path)
        studio.upload_file(file_path=file_path, remote_path=remote_path, progress_bar=True)
        return remote_path