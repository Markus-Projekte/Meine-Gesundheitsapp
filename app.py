import streamlit as st
import google.generativeai as genai
import re

# 1. SETUP
try:
    genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
    model = genai.GenerativeModel('models/gemini-3-flash-preview')
except:
    st.error("API-Key Fehler.")
    st.stop()

# 2. SEITEN-KONFIGURATION
st.set_page_config(page_title="Dein Gesundheits-Mentor", layout="wide")

# 3. DYNAMISCHES STYLING (Achtung: Farbe ändert sich bei Besserung)
if "pain_level" not in st.session_state:
    st.session_state.pain_level = 1

hue = 120 - (st.session_state.pain_level * 12)
sidebar_color = f"hsla({hue}, 70%, 95%, 1)"

st.markdown(f"""
    <style>
    [data-testid="stSidebar"] {{ background-color: {sidebar_color}; border-left: 2px solid #ddd; }}
    .self-care-box {{ background-color: #e7f3ff; padding: 15px; border-radius: 10px; border: 1px solid #b3d7ff; color: #004085; }}
    </style>
    """, unsafe_allow_html=True)

# 4. INITIALISIERUNG
if "messages" not in st.session_state:
    st.session_state.messages = []
if "anamnese_daten" not in st.session_state:
    st.session_state.anamnese_daten = {}
if "self_care_tips" not in st.session_state:
    st.session_state.self_care_tips = []

# 5. LAYOUT: CHAT & MONITORING
col_chat, col_monitor = st.columns([1.5, 1])

with col_monitor:
    st.header("📋 Analyse & Hilfe")
    
    # Sektion: Selbstbehandlung
    if st.session_state.self_care_tips:
        st.subheader("💡 Was du jetzt tun kannst:")
        for tip in st.session_state.self_care_tips:
            st.markdown(f"<div class='self-care-box'>{tip}</div>", unsafe_allow_html=True)
    
    st.markdown("---")
    st.write(f"**Aktueller Status:** {'Stabil' if st.session_state.pain_level < 4 else 'Beobachtung nötig'}")
    st.progress(st.session_state.pain_level / 10)
    
    if st.button("Gespräch neu starten"):
        st.session_state.messages = []
        st.session_state.anamnese_daten = {}
        st.session_state.self_care_tips = []
        st.rerun()

with col_chat:
    st.title("👨‍⚕️ Dein interaktiver Mentor")
    
    for m in st.session_state.messages:
        with st.chat_message(m["role"]):
            st.markdown(m["content"])

    if prompt := st.chat_input("Beschreibe kurz, wie du dich fühlst..."):
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        with st.chat_message("assistant"):
            # SYSTEM-ANWEISUNG: Interaktiver Dialog & Hilfe zur Selbsthilfe
            system_prompt = (
                "Du bist ein einfühlsamer Gesundheits-Mentor. Dein Ziel ist ein schrittweiser Dialog.\n"
                "REGELN:\n"
                "1. Stelle IMMER NUR EINE Frage pro Nachricht. Überfalle den Nutzer nicht.\n"
                "2. Wenn die Symptome mild klingen (Schmerz < 4), schlage Hausmittel oder Übungen vor.\n"
                "3. Markiere Selbsthilfe-Tipps mit < >, z.B. <Trinke heute mindestens 2 Liter Wasser>.\n"
                "4. Extrahiere Fakten in { }, z.B. {Dauer: seit heute}.\n"
                "5. Sei warmherzig. Wenn der Nutzer Schmerzen hat, sag zuerst etwas Mitfühlendes.\n"
                "6. Nur bei Warnsignalen (Red Flags) zum Arzt raten. Sonst Fokus auf Linderung."
            )
            
            # Kontext senden
            history = [{"role": "system", "parts": [system_prompt]}]
            for m in st.session_state.messages[-10:]:
                role = "model" if m["role"] == "assistant" else "user"
                history.append({"role": role, "parts": [m["content"]]})
            
            response = model.generate_content(history)
            antwort = response.text
            
            # Selbsthilfe extrahieren < >
            tips = re.findall(r"<(.*?)>", antwort)
            for t in tips:
                if t not in st.session_state.self_care_tips:
                    st.session_state.self_care_tips.append(t)
            
            # Anamnese extrahieren { }
            data = re.findall(r"\{(.*?)\}", antwort)
            for d in data:
                if ":" in d:
                    k, v = d.split(":", 1)
                    st.session_state.anamnese_daten[k.strip()] = v.strip()
                    # Schmerzlevel-Update falls vorhanden
                    if "Stärke" in k or "Level" in k:
                        try: st.session_state.pain_level = int(re.search(r'\d+', v).group())
                        except: pass

            # Text säubern
            anzeige = re.sub(r"\{.*?\}|<.*?>|\[\[.*?\]\]", "", antwort).strip()
            
            st.markdown(anzeige)
            st.session_state.messages.append({"role": "assistant", "content": anzeige})
