import streamlit as st
import requests
import base64
import os
from dotenv import load_dotenv
from concurrent.futures import ThreadPoolExecutor, as_completed

load_dotenv()

def split_text(text, chunk_size=100):
    """Split text into chunks at sentence or word boundaries"""
    if len(text) <= chunk_size:
        return [text]
    
    chunks = []
    sentence_delimiters = ['।', '.', '!', '?', '\n']
    
    current_chunk = ""
    temp = text
    for delimiter in sentence_delimiters:
        temp = temp.replace(delimiter, delimiter + '<SPLIT>')
    
    parts = temp.split('<SPLIT>')
    
    for part in parts:
        part = part.strip()
        if not part:
            continue
            
        if current_chunk and len(current_chunk) + len(part) + 1 > chunk_size:
            chunks.append(current_chunk.strip())
            current_chunk = part
        else:
            if current_chunk:
                current_chunk += " " + part
            else:
                current_chunk = part
        
        if len(current_chunk) > chunk_size:
            words = current_chunk.split()
            temp_chunk = ""
            for word in words:
                if len(temp_chunk) + len(word) + 1 <= chunk_size:
                    temp_chunk += (" " if temp_chunk else "") + word
                else:
                    if temp_chunk:
                        chunks.append(temp_chunk.strip())
                    temp_chunk = word
            current_chunk = temp_chunk
    
    if current_chunk:
        chunks.append(current_chunk.strip())
    
    return chunks if chunks else [text]

def process_chunk(chunk, chunk_index, api_url):
    """Process single chunk and return indexed result"""
    try:
        response = requests.post(api_url, json={"text": chunk}, timeout=60)
        if response.status_code == 200:
            result = response.json()
            audio_bytes = base64.b64decode(result["audio_base64"])
            return (chunk_index, audio_bytes, None)
        return (chunk_index, None, f"Status {response.status_code}: {response.text[:200]}")
    except Exception as e:
        return (chunk_index, None, f"{type(e).__name__}: {str(e)}")

def stitch_audio_bytes(audio_chunks_list):
    """Stitch multiple WAV audio byte arrays together"""
    if not audio_chunks_list:
        return b''
    if len(audio_chunks_list) == 1:
        return audio_chunks_list[0]
    
    first_chunk = audio_chunks_list[0]
    if len(first_chunk) < 44:
        return b''.join(audio_chunks_list)
    
    data_offset = first_chunk.find(b'data')
    if data_offset == -1:
        return b''.join(audio_chunks_list)
    
    audio_data_start = data_offset + 8
    
    all_audio_data = []
    for i, chunk in enumerate(audio_chunks_list):
        if i == 0:
            all_audio_data.append(chunk[audio_data_start:])
        else:
            chunk_data_offset = chunk.find(b'data')
            if chunk_data_offset != -1:
                chunk_audio_start = chunk_data_offset + 8
                all_audio_data.append(chunk[chunk_audio_start:])
            else:
                all_audio_data.append(chunk[44:] if len(chunk) > 44 else chunk)
    
    combined_audio_data = b''.join(all_audio_data)
    header = bytearray(first_chunk[:audio_data_start])
    
    new_data_size = len(combined_audio_data)
    header[audio_data_start - 4:audio_data_start] = new_data_size.to_bytes(4, 'little')
    
    new_file_size = 36 + new_data_size
    header[4:8] = new_file_size.to_bytes(4, 'little')
    
    return bytes(header) + combined_audio_data

def show():
    """Display the Text-to-Speech interface"""
    st.title("🔊 Text-to-Speech Interface")
    
    # API endpoint
    NGROK_BASE = os.getenv("NGROK_BASE_URL", "")
    
    if not NGROK_BASE:
        st.error("⚠️ NGROK_BASE_URL environment variable not set!")
        st.info("Please set it in Streamlit Cloud Secrets or your .env file")
        return
    
    API_URL = f"{NGROK_BASE}/tts/tts"
    
    with st.expander("🔧 Debug Info"):
        st.code(f"API URL: {API_URL}")
    
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
                    # Split text into chunks
                    chunks = split_text(text, chunk_size=100)
                    
                    if len(chunks) > 1:
                        st.info(f"Processing {len(chunks)} chunks...")
                    
                    # Process chunks concurrently
                    audio_results = [None] * len(chunks)
                    errors = []
                    
                    with ThreadPoolExecutor(max_workers=min(5, len(chunks))) as executor:
                        futures = {
                            executor.submit(process_chunk, chunk, i, API_URL): i 
                            for i, chunk in enumerate(chunks)
                        }
                        
                        for future in as_completed(futures):
                            chunk_index, audio_bytes, error = future.result()
                            
                            if error:
                                errors.append(f"Chunk {chunk_index + 1}: {error}")
                            elif audio_bytes:
                                audio_results[chunk_index] = audio_bytes
                    
                    # Filter out None values
                    audio_chunks = [chunk for chunk in audio_results if chunk is not None]
                    
                    if not audio_chunks:
                        st.error("❌ Failed to generate audio")
                        if errors:
                            with st.expander("Error Details"):
                                for err in errors:
                                    st.error(err)
                        return
                    
                    # Stitch if multiple chunks
                    if len(audio_chunks) > 1:
                        final_audio = stitch_audio_bytes(audio_chunks)
                    else:
                        final_audio = audio_chunks[0]
                    
                    if errors:
                        st.warning(f"⚠️ {len(errors)} chunk(s) failed but continuing with available audio")
                    
                    # Display audio player
                    st.audio(final_audio, format="audio/wav")
                    
                    # Download button
                    st.download_button(
                        label="⬇️ Download Audio",
                        data=final_audio,
                        file_name="tts_output.wav",
                        mime="audio/wav"
                    )
                    
                    st.success("✅ Audio generated!")
                    
                except requests.exceptions.ConnectionError as e:
                    st.error(f"❌ Connection Error: Could not reach {API_URL}")
                    st.error(f"Details: {str(e)}")
                except Exception as e:
                    st.error(f"❌ Error: {type(e).__name__}: {str(e)}")
                    with st.expander("Full Error Details"):
                        import traceback
                        st.code(traceback.format_exc())
        else:
            st.warning("⚠️ Please enter some text first!")
    
    # Sample texts
    with st.expander("📝 Sample Texts"):
        st.markdown("""
        - `ನಮಸ್ಕಾರ, ನೀವು ಹೇಗಿದ್ದೀರಿ?`
        - `ಇಂದು ಹವಾಮಾನ ತುಂಬಾ ಚೆನ್ನಾಗಿದೆ`
        - `ನಾನು ಕನ್ನಡ ಕಲಿಯುತ್ತಿದ್ದೇನೆ`
        """)