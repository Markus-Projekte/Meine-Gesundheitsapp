import streamlit as st
import google.generativeai as genai

# 1. SICHERE VERBINDUNG ZUM KEY (Über Streamlit Secrets)
try:
    API_KEY = st.secrets["GEMINI_API_KEY"]
    genai.configure(api_key=API_KEY)
    # Wir nutzen 1.5-flash, das ist schnell und stabil
    model = genai.GenerativeModel('gemini-pro')
except Exception as e:
    st.error("Fehler beim Laden des API-Keys. Hast du ihn in den 'Secrets' hinterlegt?")
    st.stop()

# 2. SEITEN-DESIGN
st.set_page_config(page_title="Mentor KI", page_icon="🧘")

# Falls die App neu startet, leeren wir den Speicher für den Verlauf nicht
if "messages" not in st.session_state:
    st.session_state.messages = []

# 3. NOTFALL-CHECK (Sicherheit geht vor!)
def ist_notfall(text):
    notfall_woerter = ["suizid", "atemnot", "herzinfarkt", "töten", "notfall", "vergiften"]
    return any(wort in text.lower() for wort in notfall_woerter)

# 4. DAS INTERFACE
st.title("🧘 Dein Alltags-Mentor")
st.info("Hinweis: Dies ist ein Prototyp zur Selbsthilfe. In Notfällen bitte 112 wählen.")

# Sidebar für Optionen
with st.sidebar:
    if st.button("Chat löschen"):
        st.session_state.messages = []
        st.rerun()
    st.markdown("---")
    st.write("📞 Notruf: 112")
    st.write("☎️ Seelsorge: 0800 1110111")

# 5. CHAT-LOGIK
# Den bisherigen Chat anzeigen
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# Neue Eingabe vom Nutzer
if prompt := st.chat_input("Wie kann ich dir heute helfen?"):
    
    # Nutzer-Nachricht anzeigen & speichern
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    # A. Sicherheits-Check
    if ist_notfall(prompt):
        antwort = "🚨 **WICHTIG:** Das klingt nach einer sehr ernsten Lage. Bitte suche sofort Hilfe beim Notruf (112) oder einer Rettungsstelle!"
    else:
        # B. KI-Anfrage
        try:
            with st.chat_message("assistant"):
                with st.spinner("Ich überlege..."):
                    # Instruktion an die KI
                    system_anweisung = (
                        "Du bist ein hilfreicher Mentor für den Alltag. "
                        "Antworte warmherzig, gib keine Diagnosen, sondern schlage kleine Selbsthilfe-Übungen vor. "
                        "Erinnere den Nutzer bei Symptomen immer daran, einen Arzt aufzusuchen."
                    )
                    full_prompt = f"{system_anweisung}\n\nNutzer: {prompt}"
                    
                    response = model.generate_content(full_prompt)
                    antwort = response.text
                    st.markdown(antwort)
        except Exception as e:
            antwort = "Entschuldigung, ich habe gerade ein technisches Problem. Bitte versuche es gleich noch einmal."
            st.error(f"Technischer Fehler: {e}")

    # Antwort speichern
    st.session_state.messages.append({"role": "assistant", "content": antwort})

