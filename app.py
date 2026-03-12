import streamlit as st
import google.generativeai as genai

# 1. SETUP
try:
    API_KEY = st.secrets["GEMINI_API_KEY"]
    genai.configure(api_key=API_KEY)
    model = genai.GenerativeModel('models/gemini-3-flash-preview')
except Exception as e:
    st.error("Setup Fehler. Bitte Secrets prüfen.")
    st.stop()

# 2. DESIGN & STYLING
st.set_page_config(page_title="Dein Begleiter", page_icon="🌿")
st.markdown("""
    <style>
    .stApp { background-color: #f7f9fb; }
    .stChatMessage { border-radius: 15px; }
    </style>
    """, unsafe_allow_html=True)

# 3. STATUS
if "messages" not in st.session_state:
    st.session_state.messages = []
if "care_points" not in st.session_state:
    st.session_state.care_points = 0

# 4. OBERFLÄCHE
st.title("🌿 Dein persönlicher Begleiter")

# Den Fortschritt nennen wir jetzt "Achtsamkeits-Moment"
st.write(f"Heutige Selbstfürsorge: {st.session_state.care_points}%")
st.progress(st.session_state.care_points)

# Sidebar
with st.sidebar:
    st.header("Einstellungen")
    if st.button("Gespräch neu starten"):
        st.session_state.messages = []
        st.session_state.care_points = 0
        st.rerun()
    st.info("Ich höre dir zu und wir suchen gemeinsam nach dem nächsten kleinen Schritt.")

# 5. CHAT ANZEIGEN
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# 6. DIALOG-LOGIK
if prompt := st.chat_input("Was beschäftigt dich gerade?"):
    # Punkte für die Beschäftigung mit sich selbst
    if st.session_state.care_points < 100:
        st.session_state.care_points += 10
        
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    try:
        with st.chat_message("assistant"):
            # STRENGE ANWEISUNG FÜR KURZE ANTWORTEN
            instruktion = (
                "Du bist ein achtsamer Begleiter. DEINE REGELN:\n"
                "1. Antworte extrem kurz (max. 2-3 Sätze).\n"
                "2. Gib keine langen Listen oder Ratschläge.\n"
                "3. Stelle immer nur EINE gezielte Nachfrage, um das Problem besser zu verstehen.\n"
                "4. Sei warmherzig, aber komm direkt zum Punkt.\n"
                "5. Arbeite mit dem, was der Nutzer gerade gesagt hat."
            )
            
            # Kontext (letzte 10 Nachrichten für flüssigen Dialog)
            messages_for_ai = [{"role": "system", "parts": [instruktion]}]
            for m in st.session_state.messages[-10:]:
                role = "model" if m["role"] == "assistant" else "user"
                messages_for_ai.append({"role": role, "parts": [m["content"]]})
            
            response = model.generate_content(messages_for_ai)
            antwort = response.text
            
            st.markdown(antwort)
            st.session_state.messages.append({"role": "assistant", "content": antwort})

    except Exception as e:
        st.error("Ein kleiner technischer Schluckauf. Schreib es bitte nochmal.")
