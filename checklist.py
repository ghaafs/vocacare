import os
import streamlit as st
from twilio.rest import Client

# Twilio configuration (use environment variables for security)
account_sid = os.getenv("account_sid")
auth_token = os.getenv("auth_token")
twilio_client = Client(account_sid, auth_token)

# Function to send WhatsApp message
def send_whatsapp_message(to_number, completed_items):
    try:
        message_body = (
            "Halo! Berikut adalah aktivitas yang telah Anda selesaikan hari ini:\n\n"
            + "\n".join([f"- {item}" for item in completed_items])
            + "\n\nTetap semangat dan sehat selalu! 😊"
        )

        message = twilio_client.messages.create(
            from_='whatsapp:+14155238886',  # Twilio WhatsApp Sandbox number
            body=message_body,
            to=f'whatsapp:{to_number}'
        )
        return message.sid
    except Exception as e:
        return f"Terjadi kesalahan saat mengirim pesan: {e}"

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

    # Input phone number
    phone_number = st.text_input("Masukkan nomor WhatsApp Anda (format: +62...):", "+62")

    # Save button
    if st.button("Simpan Checklist"):
        completed_items = [item for i, item in enumerate(checklist_items) if st.session_state.checklist_states[i]]
        if completed_items:
            st.success(f"Checklist tersimpan! Aktivitas selesai: {', '.join(completed_items)}")

            # Send WhatsApp message
            message_sid = send_whatsapp_message(phone_number, completed_items)
            if "SM" in message_sid:  # Check if the message SID is valid
                st.success("Pesan WhatsApp berhasil dikirim!")
            else:
                st.error(message_sid)  # Display error message
        else:
            st.warning("Tidak ada aktivitas yang ditandai selesai.")
