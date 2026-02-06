import streamlit as st
import requests
import re

# Page config
st.set_page_config(page_title="Translation Interface", page_icon="🌐")

st.title("🌐 English to Kannada Translation")

# API endpoint
API_URL = "http://localhost:8003/translate"

# --- Batching Logic Configuration ---
# Set to 2 to minimize VRAM usage and handle smaller context windows
SENTENCES_PER_BATCH = 2 

def split_into_sentences(text):
    """Splits text into sentences while keeping punctuation."""
    # This regex splits by . ! or ? but keeps the punctuation with the sentence
    sentences = re.split(r'(?<=[.!?])\s+', text)
    return [s.strip() for s in sentences if s.strip()]

def translate_batch(batch_list):
    """Sends a small batch of sentences for translation."""
    # We join with a space or newline; for IndicTrans2, newline is often safer
    combined_text = "\n".join(batch_list)
    payload = {
        "source_language": "eng_Latn",
        "text": combined_text
    }
    
    response = requests.post(API_URL, json=payload, timeout=90)
    if response.status_code == 200:
        return response.json().get('translated_text', "")
    else:
        raise Exception(f"API Error {response.status_code}: {response.text}")

# --- UI Layout ---
text = st.text_area(
    "Enter English text:",
    placeholder="The app will process this in small batches of 2 sentences each...",
    height=200
)

if st.button("Translate", type="primary"):
    if text.strip():
        # Step 1: Segmentation
        sentences = split_into_sentences(text)
        total_sentences = len(sentences)
        
        translated_segments = []
        
        # UI Progress elements
        progress_text = st.empty()
        progress_bar = st.progress(0)
        
        try:
            with st.spinner("Processing small batches..."):
                # Step 2: Batching (Step size of 2)
                for i in range(0, total_sentences, SENTENCES_PER_BATCH):
                    batch = sentences[i : i + SENTENCES_PER_BATCH]
                    
                    # Update UI feedback
                    current_batch_num = (i // SENTENCES_PER_BATCH) + 1
                    total_batches = (total_sentences + SENTENCES_PER_BATCH - 1) // SENTENCES_PER_BATCH
                    progress_text.text(f"Translating batch {current_batch_num} of {total_batches}...")
                    
                    # API Call
                    translated_output = translate_batch(batch)
                    translated_segments.append(translated_output)
                    
                    # Update progress bar
                    progress_bar.progress(min((i + SENTENCES_PER_BATCH) / total_sentences, 1.0))
                
                progress_text.text("✅ All batches processed!")
                
            # Step 3: Reassembly
            # Joining with a space to create a cohesive paragraph
            final_translation = " ".join(translated_segments)
            
            st.divider()
            st.subheader("Kannada Translation:")
            st.write(final_translation)
            
            # Copy box for the user
            st.code(final_translation, language=None)
            
        except Exception as e:
            st.error(f"❌ Translation failed: {str(e)}")
            st.info("Tip: Ensure your backend server is active and can handle the requests.")
    else:
        st.warning("⚠️ Please enter some text first!")