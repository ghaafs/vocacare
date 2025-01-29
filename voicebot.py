import os
import time
import wave
import pyaudio
import google.generativeai as genai
from google.generativeai.types import generation_types
from google.cloud import speech
from google.cloud import texttospeech
from google.oauth2 import service_account
from dotenv import load_dotenv
from datetime import datetime, timedelta
from threading import Thread
import tempfile
import matplotlib.pyplot as plt
import numpy as np
import streamlit as st
import json
import playsound

# Load environment variables
load_dotenv()

# API Keys and Credentials
gemini_api_key = os.getenv("GEMINI_API_KEY")
google_api_credentials = '/Users/ghanyfitriamaras/Documents/VOCA_LAB/voca-new-lab/VOCACARE/new.json'

# Setup for Gemini (NLP)
genai.configure(api_key=gemini_api_key)

generation_config = generation_types.GenerationConfig(
    temperature=0.7, top_p=0.9, top_k=50, max_output_tokens=1024
)
model = genai.GenerativeModel(model_name="gemini-1.5-flash", generation_config=generation_config)

# Setup for Google Speech-to-Text (STT)
speech_client = speech.SpeechClient(credentials=service_account.Credentials.from_service_account_file(google_api_credentials))

# Setup for Google Text-to-Speech (TTS)
tts_client = texttospeech.TextToSpeechClient(credentials=service_account.Credentials.from_service_account_file(google_api_credentials))

# Conversation history
conversation_history = []

# Predefined responses for common queries
predefined_responses = {
    "kesepian": "Aku di sini kok, jangan khawatir. Kamu bisa cerita apa saja ke aku.",
    "aktivitas": "Hari ini kamu bisa berjalan-jalan di sekitar rumah atau membaca buku yang sudah lama ingin kamu baca.",
    "cuaca": "Hari ini cuacanya cerah, sepertinya waktu yang tepat untuk berjalan-jalan sebentar.",
    "bosen": "Yuk, kita coba main permainan kata atau kuis singkat supaya bisa menghiburmu.",
    "belajar": "Bagaimana kalau kita mulai belajar sedikit tentang cara merawat tanaman atau resep masakan baru?",
    "kesehatan": "Menjaga kesehatan penting. Cobalah melakukan sedikit peregangan atau jalan kaki di sekitar rumah selama 10 menit setiap hari.",
    "semangat": "Semangat! Kamu sudah melakukan banyak hal hebat. Ingat, setiap hari adalah kesempatan baru untuk merasa lebih baik.",
    "obat": "Jangan khawatir, saya bisa membantu mengingatkan. Kalau sekarang waktunya minum obat, segera diminum ya. Kalau sudah, beri tahu saya supaya kita tetap teratur.",
    "capek": "Wah, mungkin tubuh perlu istirahat lebih banyak atau butuh asupan air yang cukup. Coba minum air dulu, dan kalau masih terasa capek, saya sarankan Anda berbicara dengan dokter",
    "halo": "Hai, Vocacare di sini, ada yang bisa dibantu?"
}

# Function for recording audio with live visualization
def record_audio_with_visualization(duration=8):
    with tempfile.NamedTemporaryFile(delete=False) as tmpfile:
        filename = tmpfile.name  # Use a temporary file for storing audio
        p = pyaudio.PyAudio()
        stream = p.open(format=pyaudio.paInt16, channels=1, rate=16000, input=True, frames_per_buffer=1024)

        print("Recording...")
        frames = []

        # Setup matplotlib for real-time visualization
        plt.ion()
        fig, ax = plt.subplots()
        x = np.arange(0, 1024)
        line, = ax.plot(x, np.random.rand(1024), '-')
        ax.set_ylim(-32768, 32767)
        ax.set_xlim(0, 1024)
        plt.title("Audio Input Amplitude")
        plt.xlabel("Samples")
        plt.ylabel("Amplitude")

        for _ in range(0, int(16000 / 1024 * duration)):
            data = stream.read(1024, exception_on_overflow=False)
            frames.append(data)

            # Update plot with new audio data
            audio_data = np.frombuffer(data, dtype=np.int16)
            line.set_ydata(audio_data)
            fig.canvas.draw()
            fig.canvas.flush_events()

        plt.ioff()
        plt.close(fig)

        print("Recording finished.")
        stream.stop_stream()
        stream.close()
        p.terminate()

        with wave.open(filename, 'wb') as wf:
            wf.setnchannels(1)
            wf.setsampwidth(p.get_sample_size(pyaudio.paInt16))
            wf.setframerate(16000)
            wf.writeframes(b''.join(frames))
    return filename

# Function for speech-to-text
def speech_to_text(audio_filename):
    with open(audio_filename, 'rb') as audio_file:
        content = audio_file.read()

    audio = speech.RecognitionAudio(content=content)
    config = speech.RecognitionConfig(
        encoding=speech.RecognitionConfig.AudioEncoding.LINEAR16,
        sample_rate_hertz=16000,
        language_code="id-ID"
    )

    response = speech_client.recognize(config=config, audio=audio)
    if response.results:
        return response.results[0].alternatives[0].transcript
    else:
        return ""

# Function for generating response based on predefined responses and conversation history
def generate_response(prompt):
    conversation_history.append(f"User: {prompt}")
    context = "\n".join(conversation_history[-5:])

    # Check if the user is asking about predefined topics
    for keyword, response in predefined_responses.items():
        if keyword in prompt.lower():
            conversation_history.append(f"Vocacare: {response}")
            return response

    # If the prompt is not predefined, generate a casual response using the NLP model
    casual_prompt = f"Anggap kamu sebagai teman dekat sekaligus asisten lansia. Jawab pertanyaan berikut dengan gaya kasual, ramah, dan hangat: {context}\nVocacare:"
    response = model.generate_content([casual_prompt])
    answer = response.text.strip()
    conversation_history.append(f"Vocacare: {answer}")
    return answer

# Function for text-to-speech
def text_to_speech(text, filename="output.mp3"):
    synthesis_input = texttospeech.SynthesisInput(text=text)
    voice = texttospeech.VoiceSelectionParams(language_code="id-ID", ssml_gender=texttospeech.SsmlVoiceGender.FEMALE)
    audio_config = texttospeech.AudioConfig(audio_encoding=texttospeech.AudioEncoding.MP3)

    response = tts_client.synthesize_speech(input=synthesis_input, voice=voice, audio_config=audio_config)

    with open(filename, 'wb') as out:
        out.write(response.audio_content)

    print(f"Audio saved as {filename}")
    return filename

# Streamlit UI to interact with voicebot
def voicebot_interaction():
    st.title("Vocacare Voicebot")
    st.write("Selamat datang di Vocacare, teman berbicara Anda!")
    
    if st.button('Start Voice Interaction'):
        st.write("Recording...")
        audio_filename = record_audio_with_visualization()

        st.write("Processing...")
        user_input = speech_to_text(audio_filename)
        
        if user_input:
            st.write(f"You said: {user_input}")
            response_text = generate_response(user_input)
            st.write(f"Vocacare response: {response_text}")
            
            # Generate TTS and play audio in Streamlit
            audio_file = text_to_speech(response_text, filename="response.mp3")
            st.audio(audio_file, format="audio/mp3")

            reminder_message = send_reminders()
            if reminder_message:
                st.write(f"Reminder: {reminder_message}")
                reminder_audio = text_to_speech(reminder_message, filename="reminder.mp3")
                st.audio(reminder_audio, format="audio/mp3")
        else:
            st.write("Tidak ada suara yang terdeteksi. Silakan coba lagi.")

# Function to get Jakarta time
def get_current_time():
    return datetime.utcnow() + timedelta(hours=7)

# Function for reminders with current time announcement
def send_reminders():
    current_time = get_current_time()
    reminders = {
        (23, 10): "Selamat pagi! Jangan lupa sarapan ya.",
        (12, 00): "Waktunya makan siang! Yuk, makan yang sehat.",
        (18, 00): "Waktunya minum obat! Jangan lupa ya.",
        (19, 00): "Selamat makan malam! Nikmati hidangan malam ini.",
    }
    hourly_reminder = "Jangan lupa minum air putih agar tetap terhidrasi."

    reminder_message = ""
    for (hour, minute), message in reminders.items():
        if current_time.hour == hour and current_time.minute == minute:
            reminder_message = message
            break

    if current_time.minute == 0 and current_time.hour % 2 == 0:
        reminder_message = hourly_reminder

    if reminder_message:
        time_announcement = f"Eh, sudah jam {current_time.strftime('%H:%M:%S')}."
        return f"{time_announcement} {reminder_message}"

    return ""

if __name__ == "__main__":
    voicebot_interaction()
