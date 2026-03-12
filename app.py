import streamlit as st
import google.generativeai as genai

# 1. SETUP
try:
    API_KEY = st.secrets["GEMINI_API_KEY"]
    genai.configure(api_key=API_KEY)
    
    # Wir versuchen es jetzt mit dem Namen 'models/gemini-1.5-flash'
    # Das ist die technisch präziseste Schreibweise
    model = genai.GenerativeModel('models/gemini-1.5-flash')
except Exception as e:
    st.error(f"Setup Fehler: {e}")

st.title("🧘 Dein Alltags-Mentor")

if "messages" not in st.session_state:
    st.session_state.messages = []

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

if prompt := st.chat_input("Schreib mir..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    try:
        with st.chat_message("assistant"):
            # Der Aufruf mit Fehler-Abfang
            response = model.generate_content(prompt)
            st.markdown(response.text)
            st.session_state.messages.append({"role": "assistant", "content": response.text})
    except Exception as e:
        st.error(f"Fehler: {e}")
        # Kleiner Helfer: Wir listen verfügbare Modelle auf, wenn es kracht
        st.write("Verfügbare Modelle für deinen Key:")
        for m in genai.list_models():
            if 'generateContent' in m.supported_generation_methods:
                st.write(f"- {m.name}")
