import streamlit as st
import google.generativeai as genai
import re

# ==========================================
# 1. SETUP & KONFIGURATION
# ==========================================
try:
    genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
    model = genai.GenerativeModel('models/gemini-3-flash-preview')
except:
    st.error("API-Key Konfigurationsfehler in den Secrets.")
    st.stop()

st.set_page_config(page_title="Dein Gesundheits-Mentor", layout="wide")

# ==========================================
# 2. DYNAMISCHES STYLING & CSS
# ==========================================
if "pain_level" not in st.session_state:
    st.session_state.pain_level = 1

hue = 120 - (st.session_state.pain_level * 12)
sidebar_color = f"hsla({hue}, 70%, 95%, 1)"

st.markdown(f"""
    <style>
    [data-testid="stSidebar"] {{ background-color: {sidebar_color}; border-left: 2px solid #ddd; }}
    .exercise-card {{ background-color: #ffffff; border-left: 5px solid #4CAF50; padding: 15px; border-radius: 8px; box-shadow: 2px 2px 5px rgba(0,0,0,0.1); margin-bottom: 15px; }}
    .term-explanation {{ background-color: #f0f7ff; padding: 10px; border-left: 5px solid #007bff; border-radius: 5px; margin: 5px 0; font-size: 0.9em; }}
    .emergency-box {{ background-color: #fff3cd; padding: 15px; border-radius: 10px; border: 1px solid #ffeeba; color: #856404; }}
    </style>
    """, unsafe_allow_html=True)

# ==========================================
# 3. INITIALISIERUNG DES SPEICHERS (Session State)
# ==========================================
states = {
    "messages": [],
    "anamnese_daten": {},
    "uebung_liste": [],
    "current_terms": {},
    "emergency_level": "Normal",
    "safety_cleared": False,
    "selected_region": "Nicht gewählt"
}
for key, value in states.items():
    if key not in st.session_state:
        st.session_state[key] = value

# ==========================================
# 4. RECHTS-CHECK / DISCLAIMER
# ==========================================
if "disclaimer_accepted" not in st.session_state:
    st.warning("### ⚖️ Wichtiger Hinweis & Datenschutz")
    st.write("""
    Diese App dient der Information und Vorbereitung auf ein Arztgespräch. 
    Sie stellt keine Diagnose. Übungen erfolgen auf eigene Gefahr.
    Deine Daten werden nur für diese Sitzung lokal verarbeitet und nicht gespeichert.
    """)
    if st.button("Ich akzeptiere und möchte starten"):
        st.session_state.disclaimer_accepted = True
        st.rerun()
    st.stop()

# ==========================================
# 5. LAYOUT: SIDEBAR (Tools & Protokoll)
# ==========================================
with st.sidebar:
    st.header("📍 Status & Analyse")
    
    # Notfall-Dashboard (Sanft)
    if st.session_state.emergency_level != "Normal":
        if st.session_state.emergency_level == "Bereitschaft":
            st.markdown("<div class='emergency-box'><b>ℹ️ Hinweis:</b> Bitte kontaktieren Sie den ärztlichen Bereitschaftsdienst unter <b>116 117</b>.</div>", unsafe_allow_html=True)
        elif st.session_state.emergency_level == "Notruf":
            st.markdown("<div class='emergency-box' style='background-color:#f8d7da; border-color:#f5c6cb; color:#721c24;'><b>🚨 Wichtig:</b> Bitte suchen Sie eine Notaufnahme auf oder wählen Sie <b>112</b>.</div>", unsafe_allow_html=True)
    
    # Eingabe-Tools
    st.session_state.pain_level = st.select_slider("Schmerzintensität (1-10):", options=range(1, 11), value=st.session_state.pain_level)
    
    seite = st.radio("Körperseite:", ["Vorderseite", "Rückseite"], horizontal=True)
    region = st.selectbox("Region:", ["Kopf", "Nacken", "Rücken", "Brust/Bauch", "Arme/Beine"])
    if st.button("Region & Level bestätigen"):
        st.session_state.selected_region = f"{seite} - {region}"
        st.toast("Daten wurden für den Mentor aktualisiert.")

    st.markdown("---")
    
    # Glossar
    if st.session_state.current_terms:
        st.subheader("🔍 Glossar")
        for term, desc in st.session_state.current_terms.items():
            st.markdown(f"<div class='term-explanation'><b>{term}:</b> {desc}</div>", unsafe_allow_html=True)

    # Arzt-Protokoll Export
    if st.button("📄 Arzt-Bericht kopieren"):
        protokoll = f"ANAMNESE-PROTOKOLL\nRegion: {st.session_state.selected_region}\nIntensität: {st.session_state.pain_level}/10\n"
        protokoll += "\n".join([f"{k}: {v}" for k, v in st.session_state.anamnese_daten.items()])
        st.code(protokoll)

# ==========================================
# 6. HAUPTBEREICH: CHAT & ÜBUNGEN
# ==========================================
col_chat, col_plan = st.columns([1.6, 1])

with col_plan:
    st.header("🧘 Übungsplan")
    if not st.session_state.uebung_liste:
        st.info("Hier erscheinen Übungen, sobald der Mentor diese für sicher und hilfreich erachtet.")
    else:
        for ex in st.session_state.uebung_liste:
            st.markdown(f"""<div class="exercise-card"><b>{ex['name']}</b><br><small>{ex['anleitung']}</small></div>""", unsafe_allow_html=True)

with col_chat:
    st.title("👨‍⚕️ Dein Gesundheits-Mentor")
    
    for m in st.session_state.messages:
        with st.chat_message(m["role"]):
            st.markdown(m["content"])

    if prompt := st.chat_input("Beschreibe deine Beschwerden..."):
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        with st.chat_message("assistant"):
            # SYSTEM-PROMPT: Vereint alle bisherigen Regeln
            system_prompt = (
                f"Du bist ein vorsichtiger Gesundheits-Mentor. Nutzerdaten: Region {st.session_state.selected_region}, Level {st.session_state.pain_level}.\n"
                "DEINE REGELN:\n"
                "1. Stelle immer nur EINE kurze Frage (Dialog-Modus).\n"
                "2. Prüfe auf Red Flags (Notruf/Bereitschaft). Falls kritisch, nutze [LEVEL: NOTRUF] oder [LEVEL: BEREITSCHAFT].\n"
                "3. Erkläre Fachbegriffe in [[ ]] und gib die Erklärung am Ende in { } an.\n"
                "4. Wenn sicher, schlage Übungen vor: [[ÜBUNG: Name | ANLEITUNG: Text]].\n"
                "5. Extrahiere Anamnese-Fakten in { }, z.B. {Dauer: 3 Tage}.\n"
                "6. Frage bei Schmerzen IMMER erst nach OPs oder Unfällen, bevor du Übungen vorschlägst."
            )
            
            history = [{"role": "system", "parts": [system_prompt]}]
            for m in st.session_state.messages[-10:]:
                role = "model" if m["role"] == "assistant" else "user"
                history.append({"role": role, "parts": [m["content"]]})
            
            response = model.generate_content(history)
            antwort = response.text
            
            # --- DATEN-EXTRAKTION AUS KI-ANTWORT ---
            # Level-Check
            if "[LEVEL: NOTRUF]" in antwort: st.session_state.emergency_level = "Notruf"
            elif "[LEVEL: BEREITSCHAFT]" in antwort: st.session_state.emergency_level = "Bereitschaft"
            
            # Übungen
            ex_match = re.search(r"\[\[ÜBUNG: (.*?) \| ANLEITUNG: (.*?)\]\]", antwort)
            if ex_match:
                st.session_state.uebung_liste.append({"name": ex_match.group(1), "anleitung": ex_match.group(2)})
            
            # Fakten & Glossar
            matches = re.findall(r"\{(.*?)\}", antwort)
            for match in matches:
                if ":" in match:
                    k, v = match.split(":", 1)
                    k, v = k.strip(), v.strip()
                    if k in ["Dauer", "Ort", "Art", "OP"]: st.session_state.anamnese_daten[k] = v
                    else: st.session_state.current_terms[k] = v

            # Anzeige säubern
            sauber = re.sub(r"\{.*?\}|\[\[.*?\]\]|\[LEVEL:.*?\]", "", antwort).strip()
            st.markdown(sauber)
            st.session_state.messages.append({"role": "assistant", "content": sauber})
