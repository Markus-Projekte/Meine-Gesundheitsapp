import streamlit as st
import google.generativeai as genai

# 1. KONFIGURATION
try:
    API_KEY = st.secrets["GEMINI_API_KEY"]
    genai.configure(api_key=API_KEY)
except:
    st.error("API Key fehlt in den Secrets!")
    st.stop()

# 2. DAS MODELL LADEN (Mit Sicherheitsnetz)
@st.cache_resource
def load_model():
    # Wir versuchen die stabilste Version
    return genai.GenerativeModel('gemini-1.5-flash-latest')

model = load_model()

# 3. INTERFACE
st.set_page_config(page_title="Dein Mentor", page_icon="🧘")
st.title("🧘 Dein Alltags-Mentor")

if "messages" not in st.session_state:
    st.session_state.messages = []

# Verlauf anzeigen
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
            # Der entscheidende Aufruf
            response = model.generate_content(prompt)
            # Falls die Antwort leer ist oder hakt:
            if response.text:
                full_response = response.text
            else:
                full_response = "Ich habe dich verstanden, kann aber gerade keine Antwort generieren."
            
            st.markdown(full_response)
            st.session_state.messages.append({"role": "assistant", "content": full_response})
    except Exception as e:
        st.error(f"Immer noch ein Verbindungsproblem: {e}")
        st.info("Tipp: Gehe in deine requirements.txt und stelle sicher, dass dort nur 'google-generativeai' steht.")
