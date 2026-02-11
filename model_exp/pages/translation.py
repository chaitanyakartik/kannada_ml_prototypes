import streamlit as st
import requests
import re
import os
from pathlib import Path
from dotenv import load_dotenv
from concurrent.futures import ThreadPoolExecutor, as_completed

# Load environment variables
load_dotenv()

def show():
    """Display the Translation interface"""
    
    st.title("🌍 Translation")
    
    # API endpoint
    NGROK_BASE = os.getenv("NGROK_BASE_URL", "https://your-ngrok-url.ngrok-free.app")
    API_URL = f"{NGROK_BASE}/translation/translate"
    
    # Batching configuration
    SENTENCES_PER_BATCH = 2
    
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
    
    def split_into_sentences(text):
        """Splits text into sentences while keeping punctuation."""
        sentences = re.split(r'(?<=[.!?])\s+', text)
        return [s.strip() for s in sentences if s.strip()]
    
    def translate_batch(batch_list, batch_index, source_lang, target_lang):
        """Sends a small batch of sentences for translation."""
        combined_text = "\n".join(batch_list)
        payload = {
            "source_language": source_lang,
            "target_language": target_lang,
            "text": combined_text
        }
        
        response = requests.post(API_URL, json=payload, timeout=90)
        if response.status_code == 200:
            return (batch_index, response.json().get('translated_text', ""))
        else:
            raise Exception(f"API Error {response.status_code}: {response.text}")
    
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
    
    st.info("💡 The app processes text in small batches of 2 sentences each for optimal performance")
    
    text = st.text_area(
        f"Enter {source_lang_name} text:",
        placeholder=f"Type or paste your {source_lang_name} text here...",
        height=200
    )
    
    if st.button("Translate", type="primary"):
        if text.strip():
            # Step 1: Segmentation
            sentences = split_into_sentences(text)
            total_sentences = len(sentences)
            
            if total_sentences == 0:
                st.warning("⚠️ No valid sentences found in the input text.")
                return
            
            translated_segments = []
            
            # UI Progress elements
            progress_text = st.empty()
            progress_bar = st.progress(0)
            
            try:
                with st.spinner("Processing batches concurrently..."):
                    # Step 2: Create all batches
                    batches = []
                    for i in range(0, total_sentences, SENTENCES_PER_BATCH):
                        batch = sentences[i : i + SENTENCES_PER_BATCH]
                        batch_index = i // SENTENCES_PER_BATCH
                        batches.append((batch, batch_index))
                    
                    total_batches = len(batches)
                    completed_count = 0
                    
                    # Dictionary to store results with their indices
                    results = {}
                    
                    # Step 3: Submit all batches concurrently
                    with ThreadPoolExecutor(max_workers=5) as executor:
                        # Submit all translation tasks
                        future_to_batch = {
                            executor.submit(translate_batch, batch, idx, source_lang_code, target_lang_code): idx 
                            for batch, idx in batches
                        }
                        
                        # Process completed batches
                        for future in as_completed(future_to_batch):
                            batch_idx = future_to_batch[future]
                            try:
                                result_idx, translated_text = future.result()
                                results[result_idx] = translated_text
                                completed_count += 1
                                
                                # Update UI feedback
                                progress_text.text(f"Completed {completed_count} of {total_batches} batches...")
                                progress_bar.progress(completed_count / total_batches)
                                
                            except Exception as e:
                                st.error(f"❌ Batch {batch_idx + 1} failed: {str(e)}")
                                raise
                    
                    progress_text.text("✅ All batches processed!")
                    
                # Step 3: Reassemble in correct order
                translated_segments = [results[i] for i in sorted(results.keys())]
                final_translation = " ".join(translated_segments)
                
                st.divider()
                st.subheader(f"{target_lang_name} Translation:")
                st.write(final_translation)
                
                # Copy box for the user
                st.code(final_translation, language=None)
                
            except requests.exceptions.ConnectionError:
                st.error(f"❌ Failed to connect to {API_URL}. Is the translation server running?")
            except Exception as e:
                st.error(f"❌ Translation failed: {str(e)}")
                st.info("💡 Tip: Ensure your backend server is active and can handle the requests.")
        else:
            st.warning("⚠️ Please enter some text first!")
