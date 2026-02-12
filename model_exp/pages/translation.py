import streamlit as st
import requests
import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def show():
    """Display the Translation interface"""
    
    st.title("🌍 Translation")
    
    # API endpoint
    NGROK_BASE = os.getenv("NGROK_BASE_URL", "")
    
    if not NGROK_BASE:
        st.error("⚠️ NGROK_BASE_URL environment variable not set!")
        st.info("Please set it in Streamlit Cloud Secrets or your .env file")
        return
    
    API_URL = f"{NGROK_BASE}/translation/translate"
    
    with st.expander("🔧 Debug Info"):
        st.code(f"API URL: {API_URL}")
    
    # Language options
    LANGUAGES = {
        "English": "eng_Latn",
        "Kannada": "kan_Knda",
        "Hindi": "hin_Deva",
        "Tamil": "tam_Taml",
        "Telugu": "tel_Telu",
        "Malayalam": "mal_Mlym",
        "Marathi": "mar_Deva",
        "Gujarati": "guj_Gujr",
        "Bengali": "ben_Beng",
        "Punjabi": "pan_Guru"
    }
    
    # UI Layout
    col1, col2 = st.columns(2)
    
    with col1:
        source_lang_name = st.selectbox(
            "Source Language:",
            options=list(LANGUAGES.keys()),
            index=0  # Default to English
        )
    
    with col2:
        target_lang_name = st.selectbox(
            "Target Language:",
            options=list(LANGUAGES.keys()),
            index=1  # Default to Kannada
        )
    
    source_lang_code = LANGUAGES[source_lang_name]
    target_lang_code = LANGUAGES[target_lang_name]
    
    text = st.text_area(
        f"Enter {source_lang_name} text:",
        placeholder=f"Type or paste your {source_lang_name} text here...",
        height=200
    )
    
    if st.button("Translate", type="primary"):
        if text.strip():
            with st.spinner("Translating..."):
                try:
                    payload = {
                        "source_language": source_lang_code,
                        "target_language": target_lang_code,
                        "text": text
                    }
                    
                    response = requests.post(API_URL, json=payload, timeout=120)
                    
                    if response.status_code == 200:
                        result = response.json()
                        translated_text = result.get('translated_text', '')
                        
                        if translated_text:
                            st.divider()
                            st.success("✅ Translation completed!")
                            
                            st.subheader(f"{target_lang_name} Translation:")
                            st.write(translated_text)
                            
                            # Copy box for the user
                            st.code(translated_text, language=None)
                        else:
                            st.warning("⚠️ No translation returned from the API")
                    else:
                        st.error(f"❌ API Error {response.status_code}: {response.text[:200]}")
                        
                except requests.exceptions.ConnectionError:
                    st.error(f"❌ Failed to connect to {API_URL}. Is the translation server running?")
                except requests.exceptions.Timeout:
                    st.error("❌ Request timed out. The text might be too long or the server is slow.")
                except Exception as e:
                    st.error(f"❌ Unexpected error: {type(e).__name__}: {str(e)}")
                    with st.expander("Error Details"):
                        import traceback
                        st.code(traceback.format_exc())
        else:
            st.warning("⚠️ Please enter some text first!")
