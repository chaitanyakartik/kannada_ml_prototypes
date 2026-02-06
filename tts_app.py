import streamlit as st
import requests
import base64
import io
import soundfile as sf

# Page config
st.set_page_config(page_title="TTS Interface", page_icon="🔊")

# Title
st.title("🔊 Text-to-Speech Interface")

# API endpoint
API_URL = "http://localhost:8002/tts"

# Text input
text = st.text_area(
    "Enter text to synthesize:",
    value="ನಿಮ್ಮ ಹೆಸರೇನು? ನೀವು ಏನು ಮಾಡಲು ಇಷ್ಟಪಡುತ್ತೀರಿ?",
    height=100
)

# Synthesize button
if st.button("Generate Speech", type="primary"):
    if text.strip():
        with st.spinner("Generating audio..."):
            try:
                # Make API request
                response = requests.post(
                    API_URL,
                    json={"text": text}
                )
                
                if response.status_code == 200:
                    result = response.json()
                    
                    # Decode base64 audio
                    audio_bytes = base64.b64decode(result["audio_base64"])
                    sample_rate = result["sample_rate"]
                    
                    # Display audio player
                    st.audio(audio_bytes, format="audio/wav", sample_rate=sample_rate)
                    
                    # Show audio info
                    audio_buffer = io.BytesIO(audio_bytes)
                    audio, sr = sf.read(audio_buffer)
                    duration = len(audio) / sr
                    
                    st.success(f"✅ Audio generated successfully!")
                    st.info(f"📊 Duration: {duration:.2f} seconds | Sample Rate: {sample_rate} Hz")
                    
                    # Download button
                    st.download_button(
                        label="⬇️ Download Audio",
                        data=audio_bytes,
                        file_name="tts_output.wav",
                        mime="audio/wav"
                    )
                else:
                    st.error(f"❌ Error: {response.status_code}")
                    st.error(response.text)
                    
            except Exception as e:
                st.error(f"❌ Error: {str(e)}")
    else:
        st.warning("⚠️ Please enter some text first!")
