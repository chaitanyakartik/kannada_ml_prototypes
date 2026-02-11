import streamlit as st
import requests
import base64
import io
import soundfile as sf
import os
from pathlib import Path
from dotenv import load_dotenv
import numpy as np
from concurrent.futures import ThreadPoolExecutor
load_dotenv()

def split_text(text, chunk_size=500):
    """Split text into chunks"""
    words = text.split()
    chunks = []
    current = ""
    
    for word in words:
        if len(current) + len(word) < chunk_size:
            current += word + " "
        else:
            chunks.append(current.strip())
            current = word + " "
    
    if current:
        chunks.append(current.strip())
    
    return chunks

def process_chunk(chunk, api_url):
    """Process single chunk"""
    response = requests.post(api_url, json={"text": chunk})
    if response.status_code == 200:
        result = response.json()
        audio_bytes = base64.b64decode(result["audio_base64"])
        audio_buffer = io.BytesIO(audio_bytes)
        audio_data, sr = sf.read(audio_buffer)
        return audio_data, sr
    return None, None

def show():
    """Display the Text-to-Speech interface"""
    st.title("🔊 Text-to-Speech Interface")
    
    # API endpoint
    NGROK_BASE = os.getenv("NGROK_BASE_URL")
    API_URL = f"{NGROK_BASE}/tts/tts"
    
    # Show API URL for debugging
    st.info(f"API URL: {API_URL}")
    
    # Text input
    text = st.text_area(
        "Enter text to synthesize:",
        value="ನಿಮ್ಮ ಹೆಸರೇನು? ನೀವು ಏನು ಮಾಡಲು ಇಷ್ಟಪಡುತ್ತೀರಿ?",
        height=150,
        help="Enter Kannada text to convert to speech"
    )
    
    # Synthesize button
    if st.button("Generate Speech", type="primary"):
        if text.strip():
            with st.spinner("Generating audio..."):
                try:
                    # Split if text is long
                    if len(text) > 500:
                        chunks = split_text(text)
                        st.info(f"Processing {len(chunks)} chunks...")
                        
                        # Process chunks concurrently
                        with ThreadPoolExecutor(max_workers=5) as executor:
                            results = list(executor.map(lambda c: process_chunk(c, API_URL), chunks))
                        
                        # Combine audio
                        audio_chunks = [r[0] for r in results if r[0] is not None]
                        sample_rate = results[0][1]
                        
                        # Add silence between chunks
                        silence = np.zeros(int(0.3 * sample_rate))
                        combined = []
                        for chunk in audio_chunks:
                            combined.append(chunk)
                            combined.append(silence)
                        
                        final_audio = np.concatenate(combined[:-1])  # Remove last silence
                        
                        # Convert to bytes
                        buffer = io.BytesIO()
                        sf.write(buffer, final_audio, sample_rate, format='WAV')
                        audio_bytes = buffer.getvalue()
                    
                    else:
                        # Single request for short text
                        response = requests.post(API_URL, json={"text": text})
                        
                        if response.status_code == 200:
                            result = response.json()
                            audio_bytes = base64.b64decode(result["audio_base64"])
                            sample_rate = result["sample_rate"]
                        else:
                            st.error(f"Error: {response.status_code}")
                            return
                    
                    # Display audio player
                    st.audio(audio_bytes, format="audio/wav")
                    
                    # Download button
                    st.download_button(
                        label="⬇️ Download Audio",
                        data=audio_bytes,
                        file_name="tts_output.wav",
                        mime="audio/wav"
                    )
                    
                    st.success("✅ Audio generated!")
                    
                except Exception as e:
                    st.error(f"Error: {str(e)}")
        else:
            st.warning("⚠️ Please enter some text first!")
    
    # Sample texts
    with st.expander("📝 Sample Texts"):
        st.markdown("""
        - `ನಮಸ್ಕಾರ, ನೀವು ಹೇಗಿದ್ದೀರಿ?`
        - `ಇಂದು ಹವಾಮಾನ ತುಂಬಾ ಚೆನ್ನಾಗಿದೆ`
        - `ನಾನು ಕನ್ನಡ ಕಲಿಯುತ್ತಿದ್ದೇನೆ`
        """)