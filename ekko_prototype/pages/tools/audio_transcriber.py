import logging
import os
import time
from typing import Any

# Optional imports for local transcription (only used if OpenAI API is disabled)
try:
    import torch
    from transformers import AutoModelForSpeechSeq2Seq, AutoProcessor, pipeline
    from transformers.utils import is_flash_attn_2_available
    TORCH_AVAILABLE = True
except ImportError:
    TORCH_AVAILABLE = False

logger = logging.getLogger(__name__)
# from pydub import AudioSegment  # Commented out for Python 3.13 compatibility
# from lightning_sdk import Studio  # Only needed when running on Lightning.ai


def calculate_ratio(
    audio_lengths_minutes: list[float], processing_times_seconds: list[float]
) -> float:
    """
    Calculates the average ratio of processing time to audio length for a list of audio files.

    :param audio_lengths_minutes: List of lengths of the audio files in minutes.
    :type audio_lengths_minutes: List[float]
    :param processing_times_seconds: List of times taken to process the audio files in seconds.
    :type processing_times_seconds: List[float]
    :return: Average ratio of processing time per second of audio.
    :rtype: float
    """
    assert len(audio_lengths_minutes) == len(processing_times_seconds), (
        "Lists must be of equal length"
    )
    total_ratio = 0
    for audio_length, processing_time in zip(
        audio_lengths_minutes, processing_times_seconds, strict=False
    ):
        audio_length_seconds = audio_length * 60  # Convert minutes to seconds
        ratio = processing_time / audio_length_seconds
        total_ratio += ratio
    average_ratio = total_ratio / len(audio_lengths_minutes)
    return average_ratio


def estimate_processing_time(
    audio_length_hours: int,
    audio_length_minutes: int,
    audio_length_seconds: int,
    ratio: float,
) -> str:
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
    total_audio_seconds = (
        audio_length_hours * 3600 + audio_length_minutes * 60 + audio_length_seconds
    )
    estimated_processing_seconds = total_audio_seconds * ratio

    if estimated_processing_seconds <= 60:
        return f"{estimated_processing_seconds:.2f} seconds"
    else:
        minutes = int(estimated_processing_seconds // 60)
        seconds = estimated_processing_seconds % 60
        return f"{minutes} minutes and {seconds:.2f} seconds"


class EpisodeTranscriber:
    """Transcribes podcast episodes from MP3 files."""

    def __init__(
        self,
        parent_folder: str = "./transcripts",
        model_id: str = "distil-whisper/distil-large-v3",
    ) -> None:
        """
        Initialize the transcriber with the appropriate model and device settings.

        :param parent_folder: The directory where the transcriptions will be saved.
        :type parent_folder: str
        :param model_id: The model ID for the transcription model.
        :type model_id: str
        """
        if not TORCH_AVAILABLE:
            raise ImportError(
                "torch and transformers are required for local transcription. "
                "Please install them or use OpenAI Whisper API instead by setting "
                "use_openai_whisper=True in your configuration."
            )
        self.parent_folder = parent_folder
        os.makedirs(self.parent_folder, exist_ok=True)
        self.setup_device_and_model(model_id)

    def setup_device_and_model(self, model_id: str) -> None:
        """
        Sets up device and model based on availability of GPU and Flash Attention 2.

        :param model_id: The model ID for the transcription model.
        :type model_id: str
        """
        try:
            if is_flash_attn_2_available() and torch.cuda.is_available():
                logger.info("Using Flash Attention 2 and GPU")
                device = "cuda:0"
                torch_dtype = torch.float16
                attn_implementation = "flash_attention_2"
            else:
                logger.info("Using CPU execution")
                torch_dtype = torch.float32
                device = "cpu"
                attn_implementation = None  # Don't use flash attention on CPU

            self.device = device
            self.torch_dtype = torch_dtype

            logger.info(f"Loading Whisper model: {model_id}")

            # Create model kwargs based on device
            model_kwargs = {
                "torch_dtype": self.torch_dtype,
                "low_cpu_mem_usage": True,
                "use_safetensors": True,
            }

            # Only add attn_implementation if we're using GPU
            if attn_implementation:
                model_kwargs["attn_implementation"] = attn_implementation

            self.model = AutoModelForSpeechSeq2Seq.from_pretrained(
                model_id, **model_kwargs
            ).to(self.device)

            self.processor = AutoProcessor.from_pretrained(model_id)

            self.pipe = pipeline(
                "automatic-speech-recognition",
                model=self.model,
                tokenizer=self.processor.tokenizer,
                feature_extractor=self.processor.feature_extractor,
                max_new_tokens=128,
                chunk_length_s=25,
                batch_size=16 if device == "cuda:0" else 4,  # Smaller batch for CPU
                torch_dtype=self.torch_dtype,
                device=self.device,
            )
            logger.info("Whisper model loaded successfully")
        except Exception as e:
            logger.error(f"Error setting up Whisper model: {e}")
            raise

    def transcribe(self, mp3_file: str) -> str | None:
        """
        Transcribe the given MP3 file.

        :param mp3_file: Path to the MP3 file to transcribe.
        :type mp3_file: str
        :return: Path to the transcription text file.
        :rtype: Optional[str]
        """
        try:
            if not os.path.exists(mp3_file):
                logger.error(f"Audio file not found: {mp3_file}")
                return None

            logger.info(f"Starting transcription of: {mp3_file}")
            # audio = AudioSegment.from_mp3(mp3_file)  # Commented out for Python 3.13 compatibility
            # For now, just use a placeholder duration
            # audio_length = len(audio) / 60000  # Convert milliseconds to minutes
            audio_length = 60  # Placeholder: assume 60 minutes for now

            start_time = time.time()
            outputs = self.pipe(mp3_file)
            transcription_time = time.time() - start_time

            logger.info(
                f"{audio_length} mins of audio transcribed in {transcription_time:.2f} seconds."
            )
            return self.save(outputs, mp3_file)
        except Exception as e:
            logger.error(f"Error during transcription: {e}")
            return None

    def save(self, outputs: dict[str, Any], mp3_file: str) -> str:
        """
        Save transcription to a text file.

        :param outputs: Transcription text from the model.
        :type outputs: Dict[str, Any]
        :param mp3_file: Path to the MP3 file transcribed.
        :type mp3_file: str
        :return: Path to the saved text file.
        :rtype: str
        """
        title = os.path.basename(mp3_file).split(".")[0]
        output_file = os.path.join(self.parent_folder, f"{title}.txt")
        with open(output_file, "w", encoding="utf-8") as file:
            file.write(outputs["text"])
        return output_file

    def upload(self, file_path: str) -> str:
        """
        Uploads a file to a remote server.

        :param file_path: Local path to the file to upload.
        :type file_path: str
        :return: Remote path of the uploaded file.
        :rtype: str
        """
        # studio = Studio(name='fixed-moccasin-3jhs', teamspace='ekko', user='dejandukic')  # Only needed on Lightning.ai
        # its a little confusing; but the path for the file on the remote server is somehow
        # automatically made relative to the teamspace, i suppose; thats why the dot works
        remote_path = f"/teamspace/studios/this_studio/ekko/ekko_prototype/transcripts/{os.path.basename(file_path)}"
        print("Destination:", remote_path)
        # studio.upload_file(file_path=file_path, remote_path=remote_path, progress_bar=True)  # Only needed on Lightning.ai
        return remote_path
