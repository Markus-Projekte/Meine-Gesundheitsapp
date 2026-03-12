import streamlit as st
import google.generativeai as genai

# 1. SETUP mit dem Modell aus DEINER Liste
try:
    API_KEY = st.secrets["GEMINI_API_KEY"]
    genai.configure(api_key=API_KEY)
    
    # Wir nehmen das Modell, das bei dir verfügbar ist:
    model = genai.GenerativeModel('models/gemini-3-flash-preview')
except Exception as e:
    st.error(f"Setup Fehler: {e}")

# 2. INTERFACE
st.set_page_config(page_title="Mentor KI", page_icon="🧘")
st.title("🧘 Dein Alltags-Mentor")

if "messages" not in st.session_state:
    st.session_state.messages = []

# Chat anzeigen
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# 3. CHAT-LOGIK
if prompt := st.chat_input("Wie kann ich dir heute helfen?"):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    try:
        with st.chat_message("assistant"):
            # Anfrage an das Gemini 3 Modell
            response = model.generate_content(prompt)
            st.markdown(response.text)
            st.session_state.messages.append({"role": "assistant", "content": response.text})
    except Exception as e:
        st.error(f"Hoppla, da gab es ein Problem: {e}")
