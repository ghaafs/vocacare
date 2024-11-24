import speech_recognition as sr
import google.generativeai as genai
from faster_whisper import WhisperModel
from openai import OpenAI
import pyaudio
import os
import time
import warnings
import pyttsx3  # Added for text-to-speech functionality
import io

# Filter warnings
warnings.filterwarnings("ignore", message=r"torch.utils._pytree._register_pytree_node is deprecated")

# Constants
WAKE_WORD = "gemini"
LISTENING_FOR_WAKE_WORD = True

# Whisper Model Configuration
WHISPER_SIZE = 'tiny'  # Gunakan model yang lebih kecil untuk kecepatan
NUM_CORES = os.cpu_count()
whisper_model = WhisperModel(
    WHISPER_SIZE,
    device='cpu',
    compute_type='int8',
    cpu_threads=NUM_CORES,
    num_workers=NUM_CORES
)

# API Keys Configuration
OPENAI_KEY = 'xx'
client = OpenAI(api_key=OPENAI_KEY)
GOOGLE_API_KEY = 'yy'
genai.configure(api_key=GOOGLE_API_KEY)

# Generative AI Configuration
generation_config = {
    "temperature": 0.7,
    "top_p": 1,
    "top_k": 1,
    "max_output_tokens": 2048
}

safety_settings = [
    {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_NONE"},
    {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_NONE"},
    {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_NONE"},
    {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_NONE"}
]

# Initialize Generative AI Chat
model = genai.GenerativeModel(
    "gemini-1.5-pro",
    generation_config=generation_config,
    safety_settings=safety_settings
)
convo = model.start_chat()

# Text-to-Speech Configuration
engine = pyttsx3.init()

def speak(text):
    engine.say(text)
    engine.runAndWait()

# Convert Audio to Text
def audio_to_text(audio_data):
    try:
        with io.BytesIO(audio_data.get_wav_data()) as audio_stream:
            segments, _ = whisper_model.transcribe(audio_stream)
            return ''.join(segment.text for segment in segments)
    except Exception as e:
        print(f"Error in audio_to_text: {e}")
        return ""

# Listen for Wake Word
def listen_for_wake_word(audio):
    global LISTENING_FOR_WAKE_WORD
    text_input = audio_to_text(audio)
    if WAKE_WORD in text_input.lower().strip():
        print("Wake word detected! Please speak your prompt to Gemini.")
        LISTENING_FOR_WAKE_WORD = False

# Handle User Prompt
def handle_prompt(audio):
    global LISTENING_FOR_WAKE_WORD
    try:
        prompt_text = audio_to_text(audio).strip()
        if not prompt_text:
            print("No prompt detected. Please speak again.")
            LISTENING_FOR_WAKE_WORD = True
            return

        print(f"User: {prompt_text}")
        response = convo.send_message(prompt_text).text
        print(f"Gemini: {response}")
        speak(response)
        print("\nSay 'gemini' to activate again.\n")
        LISTENING_FOR_WAKE_WORD = True
    except Exception as e:
        print(f"Error processing prompt: {e}")
        LISTENING_FOR_WAKE_WORD = True

# Callback for Recognizer
def callback(recognizer, audio):
    global LISTENING_FOR_WAKE_WORD
    if LISTENING_FOR_WAKE_WORD:
        listen_for_wake_word(audio)
    else:
        handle_prompt(audio)

# Start Listening
def start_listening():
    global LISTENING_FOR_WAKE_WORD
    recognizer = sr.Recognizer()
    source = sr.Microphone()

    with source as s:
        recognizer.adjust_for_ambient_noise(s, duration=2)
        print("\nSay 'gemini' to activate.\n")

    recognizer.listen_in_background(source, callback, phrase_time_limit=5)
    while True:
        time.sleep(0.5)

if __name__ == "__main__":
    start_listening()