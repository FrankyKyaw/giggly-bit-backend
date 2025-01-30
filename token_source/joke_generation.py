from openai import OpenAI
import openai
from tqdm import tqdm
import os
from dotenv import load_dotenv

load_dotenv(dotenv_path='./.env')

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# Load the Whisper model
model = "whisper-1"

# Specify the folder containing audio files
audio_folder = "data"

# Get a list of all segment files in the folder
def segment_to_whole():
    segment_files = sorted([f for f in os.listdir(audio_folder) if f.startswith("segment_") and f.endswith(".mp3")])

    # Initialize an empty list to store all transcriptions
    all_transcriptions = []

    # Process each audio file
    for segment_file in tqdm(segment_files, desc="Transcribing"):
        # Full path to the audio file
        audio_path = os.path.join(audio_folder, segment_file)
        
        audio_file= open(audio_path, "rb")
        
        # Get the transcription text
        transcription = client.audio.transcriptions.create(
                        model="whisper-1", 
                        file=audio_file
                        )
                        
        # Add the transcription to our list
        all_transcriptions.append(transcription.text)

        all_transcriptions.append("[laughter]")

    # Combine all transcriptions into a single string
    full_transcription = " ".join(map(str, all_transcriptions))

    # Save the full transcription to a text file
    output_file = "./data/full_transcription.txt"
    print (f"Full text with laughter tag: {full_transcription}")
    with open(output_file, "w", encoding="utf-8") as f:
        f.write(full_transcription)

    print(f"Transcription complete! Full transcription saved to {output_file}")

def analyze_text(file_path, prompt):
    # Read the content of the .txt file
    with open(file_path, 'r') as file:
        file_content = file.read()

    # Combine the file content with the customized prompt
    combined_prompt = f"{prompt}\n\n{file_content}"

    # Make the API call
    response = client.chat.completions.create(
    model="gpt-4",  # Specify the model you want to use
    messages=[
        {"role": "system", "content": "You are an assistant that analyzes text."},
        {"role": "user", "content": combined_prompt}
    ],
    max_tokens=1500,  # Adjust the number of tokens as needed
    temperature=0.7  # Adjust the temperature for creativity
    )

    # Return the response text
    return response.choices[0].message.content.strip()

def generate_joke_txt(file_path,custom_prompt):
# Customize your prompt
    # Get the analysis from the API
    response_text = analyze_text(file_path, custom_prompt)
    output_file = "./data/full_joke.txt"
    with open(output_file, "w", encoding="utf-8") as f:
        f.write(response_text)
    print (f"All jokes: {response_text}")
    return response_text
