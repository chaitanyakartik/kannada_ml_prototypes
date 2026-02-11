import streamlit as st
import requests
import io
import traceback
import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Bytecode to Kannada character mappings
BYTECODE_MAP = {
    '<0xE0><0xB2><0x94>': 'ಔ',  # Kannada letter AU
    '<0xE0><0xB2><0x8A>': 'ಊ',  # Kannada letter UU
    '<0xE0><0xB2><0x8E>': 'ಎ',  # Kannada letter E
    '<0xE0><0xB2><0x90>': 'ಐ',  # Kannada letter AI
    '<0xE0><0xB2><0xA2>': 'ಢ',  # Kannada letter DDHA
    '<0xE0><0xB2><0x9D>': 'ಝ',  # Kannada letter JHA
    '<0xE0><0xB2><0x8B>': 'ಋ',  # Kannada letter VOCALIC R
    '<0x2E>': '.',  # Period/Full stop
}


def fix_bytecodes(text):
    """Replace bytecodes with proper Kannada characters"""
    corrected = text
    for bytecode, kannada_char in BYTECODE_MAP.items():
        corrected = corrected.replace(bytecode, kannada_char)
    return corrected

def show():
    """Display the Speech-to-Text interface"""
    
    st.title("🎙️ Speech-to-Text Converter")
    
    # API endpoint
    NGROK_BASE = os.getenv("NGROK_BASE_URL", "https://your-ngrok-url.ngrok-free.app")
    API_URL = f"{NGROK_BASE}/asr/transcribe"
    
    # Language selection
    language = st.selectbox(
        "Select language:",
        ["kannada", "hindi", "english"],
        index=0,
        help="Select the language spoken in the audio"
    )
    
    st.divider()
    
    # Input method toggle
    use_file_upload = st.toggle("📁 Upload audio file instead", value=False)
    
    audio_data = None
    filename = "recording.wav"
    
    if use_file_upload:
        # File upload mode
        st.markdown("### Upload Audio File")
        uploaded_file = st.file_uploader(
            "Choose an audio file:",
            type=["wav", "mp3", "m4a", "ogg", "flac"],
            help="Upload an audio file containing speech",
            label_visibility="collapsed"
        )
        
        if uploaded_file is not None:
            st.audio(uploaded_file, format=f"audio/{uploaded_file.type.split('/')[-1]}")
            audio_data = uploaded_file.read()
            filename = uploaded_file.name
    
    else:
        # Voice recording mode
        st.markdown("### Record Your Voice")
        
        try:
            from streamlit_mic_recorder import mic_recorder
            
            # Voice recorder with start/stop button
            audio = mic_recorder(
                start_prompt="🎙️ Click to Start Recording",
                stop_prompt="⏹️ Click to Stop Recording",
                just_once=False,
                use_container_width=True,
                key="voice_recorder"
            )
            
            if audio:
                st.success("✅ Recording captured!")
                st.audio(audio['bytes'], format="audio/wav")
                audio_data = audio['bytes']
                filename = "recording.wav"
        
        except ImportError:
            st.error("❌ Voice recording requires 'streamlit-mic-recorder' package")
            st.code("pip install streamlit-mic-recorder", language="bash")
            st.info("💡 Toggle 'Upload audio file instead' to use file upload mode")
    
    st.divider()
    
    # Transcribe button
    if audio_data:
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            if st.button("🔄 Convert to Text", type="primary", use_container_width=True):
                with st.spinner("Transcribing audio..."):
                    try:
                        # Log request details
                        st.write(f"🔍 Debug: Sending {len(audio_data)} bytes to {API_URL}")
                        st.write(f"🔍 Debug: Language = {language}, Filename = {filename}")
                        
                        # Prepare file for multipart upload
                        files = {
                            'file': (filename, io.BytesIO(audio_data), 'audio/wav')
                        }
                        
                        # Prepare form data
                        data = {
                            'language': language
                        }
                        
                        # Make API request
                        response = requests.post(API_URL, files=files, data=data, timeout=60)
                        
                        # Log response
                        st.write(f"🔍 Debug: Response status = {response.status_code}")
                        st.write(f"🔍 Debug: Response headers = {dict(response.headers)}")
                        
                        if response.status_code == 200:
                            try:
                                result = response.json()
                                st.write(f"🔍 Debug: Response JSON = {result}")
                            except Exception as json_error:
                                st.error(f"❌ Failed to parse JSON response: {json_error}")
                                st.code(response.text)
                                return
                            
                            # Try different possible response formats
                            transcribed_text = (
                                result.get('text') or 
                                result.get('transcription') or 
                                result.get('transcript') or
                                ''
                            )
                            
                            # Fix bytecode errors in the transcribed text
                            if transcribed_text:
                                transcribed_text = fix_bytecodes(transcribed_text)
                            
                            if transcribed_text:
                                st.success("✅ Transcription completed!")
                                
                                # Display processing time if available
                                processing_time = result.get('processing_time', 0)
                                if processing_time:
                                    st.info(f"⏱️ Processing time: {processing_time:.2f} seconds")
                                
                                # Display transcribed text
                                st.markdown("### 📝 Transcribed Text:")
                                
                                # Show in a nice text area
                                st.text_area(
                                    "Result:",
                                    value=transcribed_text,
                                    height=150,
                                    label_visibility="collapsed"
                                )
                                
                                # Code block for easy copying
                                with st.expander("📋 Click to copy text"):
                                    st.code(transcribed_text, language=None)
                            else:
                                st.warning("⚠️ No text found in response")
                                st.write("Full response:", result)
                                
                        else:
                            st.error(f"❌ API request failed: {response.status_code}")
                            st.code(response.text)
                            
                    except requests.exceptions.ConnectionError as e:
                        st.error(f"❌ Failed to connect to {API_URL}")
                        st.error("Make sure the STT server is running on port 8001")
                        with st.expander("Show error details"):
                            st.code(traceback.format_exc())
                            
                    except requests.exceptions.Timeout:
                        st.error("❌ Request timed out. The audio file might be too long.")
                        
                    except Exception as e:
                        st.error(f"❌ An error occurred: {str(e)}")
                        with st.expander("Show full error traceback"):
                            st.code(traceback.format_exc())
    
    else:
        if use_file_upload:
            st.info("👆 Upload an audio file to get started")
        else:
            st.info("🎙️ Click the button above to start recording")
    
    # Help section
    with st.expander("ℹ️ Help & Info"):
        st.markdown("""
        **How to use:**
        1. Select the language of your speech
        2. Either record your voice or upload an audio file
        3. Click "Convert to Text" to transcribe
        
        **Supported audio formats:**
        - WAV (recommended)
        - MP3
        - M4A
        - OGG
        - FLAC
        
        **Tips for best results:**
        - Speak clearly and at a moderate pace
        - Minimize background noise
        - Keep recordings under 10 minutes for faster processing
        - Use a good quality microphone
        """)