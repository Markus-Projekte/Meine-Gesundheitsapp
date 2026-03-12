import streamlit as st
import google.generativeai as genai

# 1. SICHERE VERBINDUNG
try:
    API_KEY = st.secrets["GEMINI_API_KEY"]
    genai.configure(api_key=API_KEY)
    
    # DIESE ZEILE IST NEU UND SICHERER:
    model = genai.GenerativeModel(model_name="gemini-1.5-flash")
    
except Exception as e:
    st.error("Konfigurationsfehler. Bitte Secrets prüfen.")
    st.stop()

# 2. DESIGN & SETUP
st.set_page_config(page_title="Dein Mentor", page_icon="🧘")

if "messages" not in st.session_state:
    st.session_state.messages = []

# 3. NOTFALL-FILTER
def check_emergency(text):
    red_flags = ["suizid", "notfall", "atemnot", "herzinfarkt", "schmerzen"]
    return any(word in text.lower() for word in red_flags)

# 4. OBERFLÄCHE
st.title("🧘 Dein Alltags-Mentor")
st.caption("Ein Prototyp zur Selbsthilfe. In Notfällen 112 wählen.")

# Chat-Verlauf anzeigen
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# Eingabe
if prompt := st.chat_input("Wie kann ich helfen?"):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    if check_emergency(prompt):
        response_text = "🚨 **WICHTIG:** Bitte wende dich sofort an den Notruf (112)!"
    else:
        try:
            with st.chat_message("assistant"):
                # Hier rufen wir die KI auf
                response = model.generate_content(prompt)
                response_text = response.text
                st.markdown(response_text)
        except Exception as e:
            # Falls Google mal wieder hakt, zeigen wir eine nette Meldung
            response_text = "Ich konnte keine Verbindung aufbauen. Bitte versuche es in einer Minute noch einmal."
            st.error(f"Technischer Hinweis: {e}")

    st.session_state.messages.append({"role": "assistant", "content": response_text})
