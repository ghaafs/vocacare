import os
import time
import wave
import pyaudio
import numpy as np
import matplotlib.pyplot as plt
import streamlit as st
import subprocess
import datetime
import pandas as pd

# Import functions from voicebot.py
from voicebot import generate_response, text_to_speech, speech_to_text

# Import reminder functions from reminder.py
from reminder import set_reminder, play_reminder, log_reminder, download_log

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
        Di dalam voicebot, anda akan mendapatkan reminder yang Anda personalisasi.
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
            # Ensure the 'sos.py' script is in the correct location
            subprocess.run(["python", "sos.py"], check=True)  # Run sos.py script
            st.success("Peringatan darurat berhasil dikirim!")
        except Exception as e:
            st.error(f"Terjadi kesalahan: {e}")

# Function for the Reminder page
def show_reminder():
    st.title("\U0001F4CB Reminder - Pengingat Harian")
    st.write("""
    Fitur ini dirancang untuk membantu lansia mencatat dan mengingat aktivitas harian mereka.
    Anda bisa menambahkan pengingat harian dan melihat log aktivitas pengingat.
    """)

    # Input for reminder time and message
    time_input = st.time_input("Pilih Waktu Pengingat", value=datetime.time(9, 0))  # default jam 9 pagi
    message = st.text_input("Pesan Pengingat (misal: Waktunya minum obat)")

    if 'reminders' not in st.session_state:
        st.session_state.reminders = []

    # Add reminder button
    if st.button("Tambah Pengingat"):
        if message:
            reminder_time = datetime.datetime.combine(datetime.date.today(), time_input)
            time_to_wait = set_reminder(reminder_time, message)
            st.session_state.reminders.append((reminder_time, message))
            st.write(f"Pengingat ditambahkan untuk {reminder_time.strftime('%H:%M:%S')}.")

    # Displaying reminders with "Selesai" button
    if st.session_state.reminders:
        st.write("Daftar Pengingat Hari Ini:")
        for i, reminder in enumerate(st.session_state.reminders):
            reminder_time, reminder_msg = reminder
            col1, col2 = st.columns([0.8, 0.2])
            col1.write(f"{reminder_time.strftime('%H:%M:%S')}: {reminder_msg}")

            # Selesai button
            if col2.button("Selesai", key=f"done_{i}"):
                # Ensure correct format for log_reminder
                log_reminder({
                    "Message": reminder_msg,
                    "Status": "Selesai",
                    "Time": reminder_time
                })
                st.session_state.reminders.remove(reminder)  # Remove completed reminder
                st.write(f"Pengingat untuk {reminder_msg} pada {reminder_time.strftime('%H:%M:%S')} selesai.")

    # Display logs
    if 'log_entries' in st.session_state and st.session_state['log_entries']:
        st.write("Log Pengingat:")
        log_df = pd.DataFrame(st.session_state['log_entries'])
        st.dataframe(log_df)  # Display log as a table

        # Add button to download log as .xlsx file
        log_file = download_log()
        if log_file:
            st.download_button(
                label="Download Log Pengingat (.xlsx)",
                data=log_file,
                file_name="log_pengingat.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )
    else:
        st.write("Belum ada log pengingat.")

# Sidebar for navigation
st.sidebar.title("\U0001F5FA Menu")
st.sidebar.markdown("<div style='color: #6A5ACD; font-size: 16px;'>Pilih halaman:</div>", unsafe_allow_html=True)
page = st.sidebar.radio("", ["Home", "Voicebot", "SOS", "Reminder"], key="menu")

# Display the selected page
if page == "Home":
    show_home()
elif page == "Voicebot":
    show_voicebot()
elif page == "SOS":
    show_sos()
elif page == "Reminder":
    show_reminder()
