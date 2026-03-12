import streamlit as st
import google.generativeai as genai

# 1. SETUP
try:
    API_KEY = st.secrets["GEMINI_API_KEY"]
    genai.configure(api_key=API_KEY)
    model = genai.GenerativeModel('models/gemini-3-flash-preview')
except Exception as e:
    st.error("Bitte prüfe deine API-Key Einstellungen.")
    st.stop()

# 2. SEITEN-KONFIGURATION & STYLING
st.set_page_config(page_title="Mein Alltags-Mentor", page_icon="🌱")

# Ein bisschen CSS für ein schöneres Design
st.markdown("""
    <style>
    .stApp { background-color: #f0f4f8; }
    .main-title { color: #2c3e50; text-align: center; }
    </style>
    """, unsafe_allow_html=True)

# 3. STATUS-SPEICHER (Session State)
if "messages" not in st.session_state:
    st.session_state.messages = []
if "progress" not in st.session_state:
    st.session_state.progress = 0

# 4. OBERFLÄCHE
st.markdown("<h1 class='main-title'>🌱 Mein persönlicher Mentor</h1>", unsafe_allow_html=True)

# Fortschrittsbalken
st.write(f"Dein heutiger Fokus-Fortschritt: {st.session_state.progress}%")
st.progress(st.session_state.progress)

# Sidebar für Individualisierung
with st.sidebar:
    st.header("Dein Fokus heute")
    fokus = st.selectbox("Wobei soll ich dich begleiten?", 
                         ["Ganzheitliches Wohlbefinden", "Körperliche Beschwerden", "Stress & Entspannung", "Motivation & Fokus"])
    
    if st.button("Chat zurücksetzen"):
        st.session_state.messages = []
        st.session_state.progress = 0
        st.rerun()

# 5. CHAT-VERLAUF ANZEIGEN
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# 6. INTERAKTION
if prompt := st.chat_input("Erzähl mir, wie es dir geht..."):
    # Fortschritt erhöhen bei Interaktion
    if st.session_state.progress < 100:
        st.session_state.progress += 20
        
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    try:
        with st.chat_message("assistant"):
            # Individuelle System-Anweisung
            instruktion = (
                f"Du bist ein ganzheitlicher Mentor. Aktueller Fokus des Nutzers: {fokus}. "
                "Antworte nicht mit Standardfloskeln. Wenn der Nutzer etwas erzählt, "
                "gehe auf die Emotionen dahinter ein. Frage nach dem Umfeld (Schlaf, Stress, Ernährung), "
                "um ein Gesamtbild zu bekommen. Sei warmherzig und lösungsorientiert."
            )
            
            # Kontext zusammenbauen
            context = f"SYSTEM: {instruktion}\n"
            for m in st.session_state.messages[-5:]: # Die letzten 5 Nachrichten für den Kontext
                context += f"{m['role']}: {m['content']}\n"
            
            response = model.generate_content(context)
            antwort = response.text
            st.markdown(antwort)
            st.session_state.messages.append({"role": "assistant", "content": antwort})
            
            # Falls die Antwort eine Übung enthält, feiern wir das!
            if st.session_state.progress >= 100:
                st.balloons()
                st.success("Toll! Du hast dich heute intensiv mit dir selbst auseinandergesetzt!")

    except Exception as e:
        st.error("Verbindung zur KI unterbrochen. Bitte kurz warten.")
