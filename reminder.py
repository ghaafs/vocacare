import streamlit as st
from google.cloud import texttospeech
import os
import datetime
from apscheduler.schedulers.background import BackgroundScheduler
import playsound
import pandas as pd
import io

# Setup scheduler
scheduler = BackgroundScheduler()

# Path to your Google Cloud credentials JSON file
os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = '/Users/ghanyfitriamaras/Documents/VOCA_LAB/voca-new-lab/VOCACARE/new.json'

# Google Cloud Text-to-Speech client
client = texttospeech.TextToSpeechClient()

# Fungsi untuk memainkan pengingat dengan suara
def play_reminder(message):
    # Set up the synthesis input
    synthesis_input = texttospeech.SynthesisInput(text=message)

    # Set up voice parameters
    voice = texttospeech.VoiceSelectionParams(
        language_code="id-ID", name="id-ID-Wavenet-A"
    )

    # Set up audio configuration
    audio_config = texttospeech.AudioConfig(
        audio_encoding=texttospeech.AudioEncoding.MP3
    )

    # Perform the text-to-speech request
    response = client.synthesize_speech(
        input=synthesis_input, voice=voice, audio_config=audio_config
    )

    # Save the audio to a file
    audio_path = "reminder.mp3"
    with open(audio_path, "wb") as out:
        out.write(response.audio_content)

    # Play the audio automatically
    playsound.playsound(audio_path)

    # Log the reminder after completion
    log_reminder(message)

# Fungsi untuk menyimpan log pengingat
def log_reminder(message):
    log_entry = {
        "Pesan Pengingat": message,
        "Waktu": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }

    if 'log_entries' not in st.session_state:
        st.session_state.log_entries = []

    st.session_state.log_entries.append(log_entry)

# Fungsi untuk mengatur pengingat dan menjadwalkannya
def set_reminder(reminder_time, message):
    now = datetime.datetime.now()
    time_to_wait = (reminder_time - now).total_seconds()
    
    # Add job to scheduler
    scheduler.add_job(play_reminder, 'date', run_date=reminder_time, args=[message])
    
    return time_to_wait

# Fungsi untuk mengunduh log sebagai file Excel (.xlsx)
def download_log():
    log_df = pd.DataFrame(st.session_state.log_entries)
    if not log_df.empty:
        # Convert to Excel and download
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine="openpyxl") as writer:
            log_df.to_excel(writer, index=False, sheet_name="Log Pengingat")
        output.seek(0)
        return output
    return None

# Streamlit UI
st.title("Pengingat Kesehatan Lansia")

# Teks penjelasan
st.write("Ini adalah pengingat untuk membantu menjaga kesehatan Anda. Anda bisa mengatur waktu dan pesan pengingat untuk kegiatan Anda.")

# Input waktu reminder dengan komponen waktu
time_input = st.time_input("Pilih Waktu Pengingat", value=datetime.time(9, 0))  # default jam 9 pagi
message = st.text_input("Pesan Pengingat (misal: Waktunya minum obat)")

# Menambahkan pengingat ke daftar
if 'reminders' not in st.session_state:
    st.session_state.reminders = []

if st.button("Tambah Pengingat"):
    if message:
        reminder_time = datetime.datetime.combine(datetime.date.today(), time_input)
        time_to_wait = set_reminder(reminder_time, message)
        st.session_state.reminders.append((reminder_time, message))
        st.write(f"Pengingat ditambahkan untuk {reminder_time.strftime('%H:%M:%S')}. Pengingat akan berbunyi tepat waktu.")

# Menampilkan daftar pengingat yang sudah ditambahkan
if st.session_state.reminders:
    st.write("Daftar Pengingat Hari Ini:")
    for reminder in st.session_state.reminders:
        st.write(f"- {reminder[0].strftime('%H:%M:%S')}: {reminder[1]}")

# Tombol untuk menyelesaikan pengingat
if st.button("Selesai"):
    if st.session_state.reminders:
        st.write("Semua pengingat telah selesai.")
        log_reminder("Semua pengingat selesai untuk hari ini.")
        st.session_state.reminders.clear()  # Clear reminders after finished
    else:
        st.write("Tidak ada pengingat yang tersisa untuk hari ini.")

# Menampilkan log pengingat
if st.session_state.get("log_entries"):
    st.write("Log Pengingat:")
    log_df = pd.DataFrame(st.session_state.log_entries)
    st.dataframe(log_df)  # Display log as a table

    # Tambahkan tombol untuk download log sebagai file .xlsx
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

# Start scheduler if not running
if not scheduler.running:
    scheduler.start()

# Fitur pengingat yang terjadi setiap jam
def send_hourly_reminders():
    current_time = datetime.datetime.now()
    hourly_reminder = "Jangan lupa minum air putih agar tetap terhidrasi."

    if current_time.minute == 0 and current_time.hour % 2 == 0:  # Set reminder every 2 hours
        return hourly_reminder
    return None

# Periodik reminder setiap jam
scheduler.add_job(send_hourly_reminders, 'interval', hours=1)

