import streamlit as st
import requests
import base64
import io
import soundfile as sf
import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
env_path = Path(__file__).parent.parent / '.env'
load_dotenv(env_path)

def show():
    """Display the Text-to-Speech interface"""
    
    st.title("🔊 Text-to-Speech Interface")
    
    # API endpoint
    NGROK_BASE = os.getenv("NGROK_BASE_URL", "https://your-ngrok-url.ngrok-free.app")
    API_URL = f"{NGROK_BASE}/tts/tts"
    
    # Text input
    text = st.text_area(
        "Enter text to synthesize:",
        value="ನಿಮ್ಮ ಹೆಸರೇನು? ನೀವು ಏನು ಮಾಡಲು ಇಷ್ಟಪಡುತ್ತೀರಿ?",
        height=100,
        help="Enter Kannada text to convert to speech"
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
                        
                except requests.exceptions.ConnectionError:
                    st.error(f"❌ Failed to connect to {API_URL}. Is the TTS server running?")
                except Exception as e:
                    st.error(f"❌ Error: {str(e)}")
        else:
            st.warning("⚠️ Please enter some text first!")
    
    # Sample texts
    with st.expander("📝 Sample Kannada Texts"):
        st.markdown("""
        Try these sample texts:
        
        - `ನಮಸ್ಕಾರ, ನೀವು ಹೇಗಿದ್ದೀರಿ?` (Hello, how are you?)
        - `ಇಂದು ಹವಾಮಾನ ತುಂಬಾ ಚೆನ್ನಾಗಿದೆ` (The weather is very nice today)
        - `ನಾನು ಕನ್ನಡ ಕಲಿಯುತ್ತಿದ್ದೇನೆ` (I am learning Kannada)
        """)
