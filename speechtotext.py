import whisper
import time
import os
from pydub import AudioSegment

def load_and_transcribe(audio_file):
    # Load the Whisper model
    model = whisper.load_model("base")

    # Start timing the transcription process
    start_time = time.time()

    # Load the audio file and transcribe
    result = model.transcribe(audio_file, word_timestamps=True)

    # Calculate transcription time
    elapsed_time = time.time() - start_time

    # Load audio to get duration using pydub (requires ffmpeg)
    audio = AudioSegment.from_file(audio_file)
    length_seconds = len(audio) / 1000

    # Store result and metadata
    transcription_result = {
        'file': audio_file,
        'transcription': result["text"],
        'transcription_time': elapsed_time,
        'audio_length': length_seconds
    }

    print(f"File: {audio_file}")
    print(f"Transcription: {result}")
    print(f"Transcription took: {elapsed_time:.2f} seconds")
    print(f"Length of audio: {length_seconds} seconds\n")

    return transcription_result

# Run the transcription function
transcriptions = load_and_transcribe("test_audio.mp3")
