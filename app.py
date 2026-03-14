import streamlit as st
import google.generativeai as genai
import re

# 1. SETUP
try:
    genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
    model = genai.GenerativeModel('models/gemini-3-flash-preview')
except:
    st.error("API-Key Fehler. Bitte in den Secrets prüfen.")
    st.stop()

# 2. SEITEN-KONFIGURATION
st.set_page_config(page_title="Med-Triage & Checkliste", layout="wide")

# 3. DYNAMISCHES STYLING
if "pain_level" not in st.session_state:
    st.session_state.pain_level = 1

hue = 120 - (st.session_state.pain_level * 12)
sidebar_color = f"hsla({hue}, 70%, 90%, 1)"

st.markdown(f"""
    <style>
    [data-testid="stSidebar"] {{ background-color: {sidebar_color}; }}
    .checklist-box {{ background-color: #fff4e6; padding: 15px; border-left: 5px solid #fd7e14; border-radius: 5px; color: #856404; }}
    .term-explanation {{ background-color: #f0f7ff; padding: 10px; border-left: 5px solid #007bff; border-radius: 5px; margin: 5px 0; }}
    </style>
    """, unsafe_allow_html=True)

# 4. INITIALISIERUNG
if "messages" not in st.session_state:
    st.session_state.messages = []
if "anamnese_daten" not in st.session_state:
    st.session_state.anamnese_daten = {}
if "checkliste" not in st.session_state:
    st.session_state.checkliste = []
if "current_terms" not in st.session_state:
    st.session_state.current_terms = {}

if "disclaimer_accepted" not in st.session_state:
    st.warning("### ⚖️ Wichtiger Hinweis")
    st.write("Diese App dient der Vorbereitung auf ein Arztgespräch. Sie ersetzt keine Diagnose.")
    if st.button("Verstanden & Starten"):
        st.session_state.disclaimer_accepted = True
        st.rerun()
    st.stop()

# 5. LAYOUT
col_chat, col_tools = st.columns([1.5, 1])

with col_tools:
    st.header("📋 Arzt-Vorbereitung")
    
    # Sektion 1: Checkliste
    if st.session_state.checkliste:
        st.subheader("Ihre Checkliste für den Arzt:")
        for item in st.session_state.checkliste:
            st.markdown(f"- [ ] {item}")
    else:
        st.info("Die Checkliste wird während des Gesprächs erstellt.")

    st.markdown("---")
    
    # Sektion 2: Fachbegriffe
    if st.session_state.current_terms:
        st.subheader("Glossar:")
        for term, desc in st.session_state.current_terms.items():
            st.markdown(f"<div class='term-explanation'><b>{term}:</b> {desc}</div>", unsafe_allow_html=True)

    st.markdown("---")
    
    # Sektion 3: Status & Kopieren
    st.write(f"**Schmerzlevel:** {st.session_state.pain_level}/10")
    if st.button("Gesamt-Bericht kopieren"):
        protokoll = f"ANAMNESE-BERICHT\nSchmerz: {st.session_state.pain_level}/10\n"
        protokoll += "\n".join([f"{k}: {v}" for k, v in st.session_state.anamnese_daten.items()])
        protokoll += "\n\nCHECKLISTE FÜR DAS GESPRÄCH:\n" + "\n".join([f"- {i}" for i in st.session_state.checkliste])
        st.code(protokoll, language="text")

with col_chat:
    st.title("👨‍⚕️ Digitaler Med-Begleiter")
    
    for m in st.session_state.messages:
        with st.chat_message(m["role"]):
            st.markdown(m["content"])

    if prompt := st.chat_input("Was sind Ihre Beschwerden?"):
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        with st.chat_message("assistant"):
            system_prompt = (
                "Du bist ein medizinischer Triage-Assistent. Dein Ziel ist eine strukturierte Anamnese.\n"
                "AUFGABEN:\n"
                "1. Nutze Fachbegriffe in [[ ]], z.B. [[Analgetika]].\n"
                "2. Erkläre Begriffe am Ende in { } z.B. {Analgetika: Schmerzmittel}.\n"
                "3. Extrahiere Anamnese-Fakten in { } z.B. {Dauer: 2 Tage}.\n"
                "4. Erstelle basierend auf dem Gespräch Punkte für eine Checkliste in < >, "
                "z.B. <Fragen Sie nach einer Überweisung zum Radiologen> oder <Erwähnen Sie die Medikamente X>.\n"
                "5. Halte dich kurz und frage gezielt nach (OPQRST-Schema)."
            )
            
            history = [{"role": "system", "parts": [system_prompt]}]
            for m in st.session_state.messages[-6:]:
                role = "model" if m["role"] == "assistant" else "user"
                history.append({"role": role, "parts": [m["content"]]})
            
            response = model.generate_content(history)
            antwort = response.text
            
            # 1. Checklisten-Extraktion < >
            cl_matches = re.findall(r"<(.*?)>", antwort)
            for item in cl_matches:
                if item not in st.session_state.checkliste:
                    st.session_state.checkliste.append(item)
            
            # 2. Fachbegriffe & Anamnese { }
            data_matches = re.findall(r"\{(.*?)\}", antwort)
            for match in data_matches:
                if ":" in match:
                    k, v = match.split(":", 1)
                    k, v = k.strip(), v.strip()
                    if len(v) < 40: # Kurze Einträge sind Anamnese oder Begriffe
                        if k in ["Dauer", "Ort", "Stärke", "Ausstrahlung"]:
                            st.session_state.anamnese_daten[k] = v
                        else:
                            st.session_state.current_terms[k] = v
            
            # Text säubern für die Anzeige
            anzeige = re.sub(r"\[\[(.*?)\]\]", r"**\1**", antwort)
            anzeige = re.sub(r"\{.*?\}", "", anzeige)
            anzeige = re.sub(r"<.*?>", "", anzeige)
            
            st.markdown(anzeige)
            st.session_state.messages.append({"role": "assistant", "content": anzeige})
