import os
import time
import asyncio
import threading
import json
import edge_tts
import pygame
import sounddevice as sd
import google.generativeai as genai
from vosk import KaldiRecognizer, Model
from google.api_core.exceptions import ResourceExhausted
from dotenv import load_dotenv

# Load environment variables from .env file if it exists
load_dotenv()

# Check if GEMINI_API_KEY is set in the environment
if "GEMINI_API_KEY" in os.environ:
    api_key = os.environ["GEMINI_API_KEY"]
else:
    api_key = "YOUR_API_KEY"  # Fallback to user-replaced API key

# Configure Gemini with the determined API key
genai.configure(
    api_key=api_key,
)
# Configure the generation AI model response variables
generation_config = {
    "temperature": 1,
    "top_p": 0.95,
    "top_k": 64,
    "max_output_tokens": 8192,
    "response_mime_type": "text/plain",
}

# Configure the AI model name, safety settings, and directives
model = genai.GenerativeModel(
    model_name="gemini-1.5-pro-latest",
    safety_settings="BLOCK_NONE",
    generation_config=generation_config,
    system_instruction=" ",
)

chat_session = model.start_chat(history=[])

# Initialize Vosk recognizer
model_path = "vosk-model-small-en-us-0.15"
recognizer = KaldiRecognizer(Model(model_path), 16000)

# Initialize pygame mixer
pygame.mixer.init()

# Function to recognize speech from the microphone
def recognize_speech():
    print("Listening...")
    recognized_text = ""
    stop_listening = False

    def callback(indata, frames, time, status):
        nonlocal recognized_text, stop_listening
        if not stop_listening and recognizer.AcceptWaveform(bytes(indata)):
            result = json.loads(recognizer.Result())
            recognized_text = result.get("text", "")
            stop_listening = True

    with sd.RawInputStream(samplerate=16000, blocksize=8000, dtype='int16', channels=1, callback=callback):
        while not stop_listening:
            if recognized_text:
                return recognized_text

# Keywords for voice and text mode to be used to toggle between them.
VOICE_MODE_KEYWORD = "voice mode"
TEXT_MODE_KEYWORD = "text mode"
EXIT_MODE_KEYWORD = "exit mode"

# Asynchronous function to convert AI response from text to speech
async def text_to_speech(text, filename="response.mp3"):
    communicate = edge_tts.Communicate(text, voice="en-US-AvaNeural")
    await communicate.save(filename)

# Asynchronous function to run text to speech and play back model audio response
async def speak(text):
    await text_to_speech(text)
    pygame.mixer.music.load("response.mp3")
    pygame.mixer.music.play()
    while pygame.mixer.music.get_busy():  # Wait for playback to finish
        await asyncio.sleep(0.1)

# Function to send a message with retry handling
def send_message_with_retry(message, max_retries=3, retry_delay=5):
    for attempt in range(max_retries):
        try:
            response = chat_session.send_message(message)
            return response
        except ResourceExhausted as e:
            print(f"Resource Exhausted: {e}")
            if attempt < max_retries - 1:
                print(f"Retrying in {retry_delay} seconds...")
                time.sleep(retry_delay)
            else:
                raise  # Re-raise the exception if all retries fail

# Main loop, now wrapped in an async function
async def main():
    voice_mode = False  # Start in text mode
    while True:
        if voice_mode:
            try:
                # Recognize speech and get text
                user_input = recognize_speech()
                print("You said: " + user_input)

                # Check for keywords or exit
                if TEXT_MODE_KEYWORD in user_input.lower() or EXIT_MODE_KEYWORD in user_input.lower():
                    voice_mode = False
                    print("Switching to text mode.")
                else:
                    # Send non-keyword text to the Gemini API with retry handling
                    response = send_message_with_retry(user_input)
                    print("\nModel: " + response.text)

                    # Convert the AI model responses to speech only while in voice mode
                    speak_task = asyncio.create_task(speak(response.text))
                    await asyncio.gather(speak_task)  # Explicitly await the speak task

            except Exception as e:
                print(f"An error occurred: {e}")
        else:
            user_input = input("User: ")
            if user_input.lower() == EXIT_MODE_KEYWORD:
                break

            # Check for mode switching keywords in user input
            if VOICE_MODE_KEYWORD in user_input.lower():
                voice_mode = True
                print("Switching to voice mode.")
            else:
                # Process user text input with retry handling
                response = send_message_with_retry(user_input)
                print("\nModel: " + response.text)
                # No TTS in text mode

    print("\nGoodbye!")

# Run the async main function
if __name__ == "__main__":
    asyncio.run(main())
