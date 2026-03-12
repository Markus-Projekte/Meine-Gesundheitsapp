import streamlit as st
import google.generativeai as genai

# 1. KONFIGURATION & KI-START
# Statt: API_KEY = "AIzaSyD3bp4VQN7aNO7Ugw0aFudEk-leZ-7Puxo"
# Schreibst du:
API_KEY = st.secrets["GEMINI_API_KEY"]
genai.configure(api_key=API_KEY)
model = genai.GenerativeModel('gemini-1.5-flash')

st.set_page_config(page_title="Mentor KI", page_icon="🧘", layout="centered")

# 2. DAS GEDÄCHTNIS (Session State)
if "messages" not in st.session_state:
    st.session_state.messages = [] # Hier werden alle Nachrichten gespeichert

# 3. NOTFALL-CHECK FUNKTION
def check_emergency(text):
    flags = ["notfall", "suizid", "atemnot", "schmerzen", "blutung"]
    return any(word in text.lower() for word in flags)

# 4. DAS DESIGN (Sidebar & Kopfzeile)
with st.sidebar:
    st.title("Einstellungen ⚙️")
    if st.button("Gespräch zurücksetzen"):
        st.session_state.messages = []
        st.rerun()
    st.markdown("---")
    st.write("📞 **Hilfe:** 112")
    st.write("☎️ **Seelsorge:** 0800 1110111")

st.title("🧘 Dein Alltags-Mentor")
st.caption("Ein Prototyp für mehr Selbstwirksamkeit im Alltag.")

# 5. DER CHAT-VERLAUF ANZEIGEN
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# 6. NEUE EINGABE
if prompt := st.chat_input("Wie fühlst du dich gerade?"):
    
    # Nutzer-Nachricht anzeigen & speichern
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    # Sicherheit prüfen
    if check_emergency(prompt):
        response_text = "🚨 **HINWEIS:** Das klingt nach einer ernsten Situation. Bitte wende dich sofort an einen Arzt oder den Notruf (112)!"
    else:
        # KI-Antwort generieren
        with st.chat_message("assistant"):
            with st.spinner("Ich bin bei dir..."):
                # Wir geben der KI den ganzen bisherigen Chat mit!
                full_prompt = f"Du bist ein Empowerment-Coach. Hilf dem Nutzer bei: {prompt}. Antworte kurz, warmherzig und gib einen Tipp zur Selbsthilfe."
                response = model.generate_content(full_prompt)
                response_text = response.text
                st.markdown(response_text)
    
    # KI-Antwort speichern

    st.session_state.messages.append({"role": "assistant", "content": response_text})
