import streamlit as st
import google.generativeai as genai
from streamlit_mic_recorder import mic_recorder
import time

# --- Page Config & Styling ---
st.set_page_config(page_title="Voice Bot", page_icon="🎙️")

st.markdown("""
    <style>
    .stChatMessage { border-radius: 15px; margin-bottom: 10px; }
    .stButton button { border-radius: 20px; }
    </style>
""", unsafe_allow_html=True)

# --- Initialization ---
if "messages" not in st.session_state:
    st.session_state.messages = []
if "settings" not in st.session_state:
    st.session_state.settings = {"api_key": "", "use_tts": True}

# --- Sidebar (Settings) ---
with st.sidebar:
    st.title("⚙️ Settings")
    api_key = st.text_input("Gemini API Key", type="password", value=st.session_state.settings["api_key"])
    use_tts = st.toggle("Enable Text-to-Speech", value=st.session_state.settings["use_tts"])
    
    if api_key:
        st.session_state.settings["api_key"] = api_key
        genai.configure(api_key=api_key)
    
    st.session_state.settings["use_tts"] = use_tts

    if st.button("Clear Conversation"):
        st.session_state.messages = []
        st.rerun()

# --- Core Logic ---
def call_llm(prompt):
    if not st.session_state.settings["api_key"]:
        return "Please enter an API Key in the settings to get a response."
    try:
        model = genai.GenerativeModel('gemini-pro')
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        return f"❌ Error: {str(e)}"

def process_audio(audio_data):
    # In a production app, you'd send 'audio_data' to an ASR API (like Whisper or Google Speech-to-Text)
    # Since the original React code used a local server at :8001, we simulate the transcription here.
    return "This is a simulated transcription. (To get real text, integrate an ASR API here)."

# --- Main UI ---
st.title("🎙️ Voice Bot")

# Display Chat History
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.write(message["content"])

# --- Input Area ---
footer = st.container()
with footer:
    cols = st.columns([1, 8, 1])
    
    with cols[0]:
        # Recording Component
        audio = mic_recorder(
            start_prompt="🎙️",
            stop_prompt="🛑",
            key="recorder"
        )

    with cols[1]:
        text_input = st.chat_input("Type a message...")

    # Handle Text Input
    if text_input:
        st.session_state.messages.append({"role": "user", "content": text_input})
        with st.chat_message("user"):
            st.write(text_input)
            
        response = call_llm(text_input)
        
        st.session_state.messages.append({"role": "assistant", "content": response})
        with st.chat_message("assistant"):
            st.write(response)
        st.rerun()

    # Handle Audio Input
    if audio:
        # Note: audio['bytes'] contains the WAV data
        with st.spinner("Transcribing..."):
            # Here you would typically use: transcription = your_asr_function(audio['bytes'])
            transcription = "User sent an audio message (requires ASR integration)" 
            
            st.session_state.messages.append({"role": "user", "content": transcription})
            response = call_llm(transcription)
            st.session_state.messages.append({"role": "assistant", "content": response})
            st.rerun()