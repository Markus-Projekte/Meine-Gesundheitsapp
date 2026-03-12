import streamlit as st
import google.generativeai as genai
import os

# 1. KONFIGURATION
try:
    API_KEY = st.secrets["GEMINI_API_KEY"]
    # Dieser Befehl zwingt die App, die stabile Version 1 zu nutzen
    os.environ["GOOGLE_API_USE_MTLS"] = "never" 
    genai.configure(api_key=API_KEY)
    
    # Wir nehmen jetzt 'gemini-1.5-flash' – das ist das Standardmodell
    model = genai.GenerativeModel('gemini-1.5-flash')
except Exception as e:
    st.error(f"Fehler bei der Konfiguration: {e}")
    st.stop()

# 2. INTERFACE
st.set_page_config(page_title="Dein Mentor", page_icon="🧘")
st.title("🧘 Dein Alltags-Mentor")

if "messages" not in st.session_state:
    st.session_state.messages = []

# Chat anzeigen
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# Eingabe
if prompt := st.chat_input("Schreib mir etwas..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    try:
        with st.chat_message("assistant"):
            # Wichtig: Wir nutzen hier den einfachsten Aufruf ohne Schnickschnack
            response = model.generate_content(prompt)
            st.markdown(response.text)
            st.session_state.messages.append({"role": "assistant", "content": response.text})
    except Exception as e:
        st.error(f"Technisches Detail-Problem: {e}")
        st.info("Falls dieser Fehler 404 bleibt, müssen wir einmal die 'Reboot App' Funktion nutzen.")
