import os
import time
import wave
import pyaudio
import numpy as np
import matplotlib.pyplot as plt
import streamlit as st
import subprocess

# Import functions from voicebot.py
from voicebot import generate_response, text_to_speech, speech_to_text

# Function for recording audio with live visualization
def record_audio_with_visualization(filename="input.wav", duration=8):
    p = pyaudio.PyAudio()
    stream = p.open(format=pyaudio.paInt16, channels=1, rate=16000, input=True, frames_per_buffer=1024)

    st.write("**\U0001F3A4 Rekaman dimulai... Silakan berbicara!**")
    frames = []

    # Setup matplotlib for real-time visualization
    fig, ax = plt.subplots()
    x = np.arange(0, 1024)
    line, = ax.plot(x, np.random.rand(1024), '-', color="#DC143C")  # Soft red line
    ax.set_ylim(-32768, 32767)
    ax.set_xlim(0, 1024)
    plt.title("Amplitudo Input Suara", fontsize=14, color="#0E1351")  # Elegant blue title
    plt.xlabel("Sampel", fontsize=12, color="#6E74B9")  # Soft purple labels
    plt.ylabel("Amplitudo", fontsize=12, color="#6E74B9")

    # Display the plot in Streamlit
    plot_placeholder = st.empty()  # Placeholder for dynamic plot

    for _ in range(0, int(16000 / 1024 * duration)):
        data = stream.read(1024, exception_on_overflow=False)
        frames.append(data)

        # Convert data to numpy array for audio data analysis
        audio_data = np.frombuffer(data, dtype=np.int16)  # Convert to numpy array

        # Update plot with new audio data
        line.set_ydata(audio_data)
        plot_placeholder.pyplot(fig)  # Dynamically update the plot

        time.sleep(0.05)  # Small delay to simulate real-time update

    plt.close(fig)

    stream.stop_stream()
    stream.close()
    p.terminate()

    with wave.open(filename, 'wb') as wf:
        wf.setnchannels(1)
        wf.setsampwidth(p.get_sample_size(pyaudio.paInt16))
        wf.setframerate(16000)
        wf.writeframes(b''.join(frames))

# Function for the Home page
def show_home():
    st.title("\U0001F916 Vocacare - Asisten Suara untuk Lansia")
    st.markdown("""
    <div style="font-size: 18px; line-height: 2; color: #4B0082;">
        Selamat datang di Vocacare! 
        Aplikasi ini dirancang khusus untuk mendukung kebutuhan lansia melalui interaksi suara yang mudah digunakan.
        Di dalam voicebot, anda akan mendapatkan reminder yang telah dipersonalisasi.
        Anda juga dapat menggunakan fitur "Tombol SOS" untuk situasi darurat.
        <br><br>
        Silakan pilih fitur dari menu navigasi di samping untuk memulai.
    </div>
    """, unsafe_allow_html=True)

# Function for the Voice Interaction page
def show_voicebot():
    st.title("\U0001F4E2 Voicebot")
    st.write("Klik tombol di bawah untuk memulai interaksi suara.")

    if st.button("\U0001F50A Mulai", key="start_voice"):
        st.write("\U0001F399 Silakan berbicara...")
        record_audio_with_visualization("input.wav")  # Record and visualize the audio
        user_input = speech_to_text("input.wav")  # Convert the audio to text

        if user_input:
            st.write(f"**Kamu berkata:** {user_input}")
            response_text = generate_response(user_input)
            st.write(f"**Balasan Vocacare:** {response_text}")
            audio_file = text_to_speech(response_text, filename="output.mp3")  # Generate TTS
            st.audio(audio_file)  # Play the response audio

# Function for the SOS page
def show_sos():
    st.title("\U0001F198 SOS - Alarm Darurat")
    st.markdown("""
    <div style="font-size: 18px; color: #DC143C; line-height: 2;">
        Klik tombol di bawah untuk mengirimkan peringatan darurat kepada kontak penting Anda.
    </div>
    """, unsafe_allow_html=True)

    if st.button("\U0001F6A8 Kirim SOS", key="send_sos"):
        st.write("\U0001F4E8 Mengirimkan peringatan darurat... Harap tunggu!")
        try:
            subprocess.run(["python", "sos.py"])  # Run sos.py script
            st.success("Peringatan darurat berhasil dikirim!")
        except Exception as e:
            st.error(f"Terjadi kesalahan: {e}")

# Function for the Checklist Reminder page
def show_checklist():
    st.title("\U0001F4CB Checklist Reminder - Pengingat Harian")
    st.write("""
    Fitur ini dirancang untuk membantu lansia mencatat dan mengingat aktivitas harian mereka.
    Tandai aktivitas yang sudah selesai dilakukan.
    """)

    # Default checklist items
    checklist_items = [
        "Minum obat pagi",
        "Melakukan senam ringan",
        "Minum air putih",
        "Makan siang",
        "Istirahat siang",
        "Minum obat malam",
        "Persiapan tidur"
    ]

    # Load checklist state from session state
    if "checklist_states" not in st.session_state:
        st.session_state.checklist_states = [False] * len(checklist_items)

    # Display checklist
    for i, item in enumerate(checklist_items):
        st.session_state.checklist_states[i] = st.checkbox(item, value=st.session_state.checklist_states[i])

    # Save button
    if st.button("Simpan Checklist"):
        completed_items = [item for i, item in enumerate(checklist_items) if st.session_state.checklist_states[i]]
        st.success(f"Checklist tersimpan! Aktivitas selesai: {', '.join(completed_items)}")

# Sidebar for navigation
st.sidebar.title("\U0001F5FA Menu")
st.sidebar.markdown("<div style='color: #6A5ACD; font-size: 16px;'>Pilih halaman:</div>", unsafe_allow_html=True)
page = st.sidebar.radio("", ["Home", "Voicebot", "SOS", "Checklist Reminder"], key="menu")

# Display the selected page
if page == "Home":
    show_home()
elif page == "Voicebot":
    show_voicebot()
elif page == "SOS":
    show_sos()
elif page == "Checklist Reminder":
    show_checklist()

# Add visual style
st.markdown("""
    <style>
        body {
            background-color: #F0F8FF; /* Light blue background */
            color: #4B0082; /* Indigo text */
        }
        .stButton>button {
            font-size: 18px;
            padding: 15px 30px;
            color: white;
            background-color: #20B2AA; /* Tosca green */
            border: none;
            border-radius: 10px;
        }
        .stButton>button:hover {
            background-color: #5F9EA0; /* Slightly darker tosca */
        }
        .stSidebar {
            background-color: ##0E1351; /* Soft purple */
        }
        .stSidebar .css-1aumxhk {
            color: white; /* White text for sidebar */
        }
    </style>
""", unsafe_allow_html=True)