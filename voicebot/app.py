import streamlit as st
import requests
import base64
import io
import os
import json
import hashlib
import time
import atexit
from pathlib import Path
from datetime import datetime
from dotenv import load_dotenv
from google import genai
from google.oauth2 import service_account
from google.genai.types import GenerateContentConfig

# --- Configuration & Setup ---

load_dotenv()

# Constants
NGROK_BASE_URL = os.getenv("NGROK_BASE_URL", "https://your-ngrok-url.ngrok-free.app")
STT_API_URL = f"{NGROK_BASE_URL}/asr/transcribe"
TTS_API_URL = f"{NGROK_BASE_URL}/tts/tts"  # Fixed: was /tts/tts, should be /tts

# Get the directory where this script is located
SCRIPT_DIR = Path(__file__).parent

# Try relative paths, fallback to voicebot/ prefix if not found
CONTEXT_FILE = SCRIPT_DIR / "data" / "master.json"
if not CONTEXT_FILE.exists():
    CONTEXT_FILE = SCRIPT_DIR / "voicebot" / "data" / "master.json"

MESSAGES_FILE = SCRIPT_DIR / "data" / "messages.json"
if not MESSAGES_FILE.parent.exists():
    MESSAGES_FILE = SCRIPT_DIR / "voicebot" / "data" / "messages.json"

# Audio storage directory
AUDIO_STORAGE_DIR = SCRIPT_DIR / "audio_cache"
if not AUDIO_STORAGE_DIR.exists():
    alt_audio_dir = SCRIPT_DIR / "voicebot" / "audio_cache"
    if alt_audio_dir.exists():
        AUDIO_STORAGE_DIR = alt_audio_dir
AUDIO_STORAGE_DIR.mkdir(exist_ok=True, parents=True)

# --- Gemini Client Setup ---

SCOPES = ["https://www.googleapis.com/auth/cloud-platform"]

if os.getenv("GCP_SA_JSON"):
    sa_info = json.loads(os.getenv("GCP_SA_JSON"))
    creds_1 = service_account.Credentials.from_service_account_info(sa_info, scopes=SCOPES)
    creds_2 = service_account.Credentials.from_service_account_info(sa_info, scopes=SCOPES)

elif os.getenv("GCP_SA_PATH"):
    creds_1 = service_account.Credentials.from_service_account_file(
        os.getenv("GCP_SA_PATH"), scopes=SCOPES
    )
    creds_2 = service_account.Credentials.from_service_account_file(
        os.getenv("GCP_SA_PATH"), scopes=SCOPES
    )

else:
    raise ValueError("Either GCP_SA_JSON or GCP_SA_PATH must be set")

SA_CLIENTS = {
    "SA_1": genai.Client(
        vertexai=True,
        project="certain-perigee-466307-q6",
        location="us-central1",
        credentials=creds_1
    ),
    "SA_2": genai.Client(
        vertexai=True,
        project="certain-perigee-466307-q6",
        location="us-central1",
        credentials=creds_2
    ),
}

# Master Instructions
MASTER_INSTRUCTIONS = """
You are an AI assistant working for a Government of Karnataka department.

You have been provided with official government documents, circulars, and policy texts as context. 
You MUST base your answers strictly on the given documents.

All user input text will be in Kannada.
You MUST respond ONLY in Kannada.
Do NOT use English in responses.

NOTE: There may be some typing mistakes or improperly formed words in the user input due to speech-to-text errors. Use your understanding of Kannada language and context to interpret the intended meaning as best as you can.

Your response MUST always be in the following JSON format:

{
  "answer": "<Kannada response here>",
  "source_reference": "<brief reference to which document or section was used>"
}

If the information is not present in the provided documents, reply with:

{
  "answer": "ಲಭ್ಯವಿರುವ ದಾಖಲೆಗಳಲ್ಲಿ ಈ ಮಾಹಿತಿಯಿಲ್ಲ.",
  "source_reference": "N/A"
}
"""

# Bytecode to Kannada character mappings
BYTECODE_MAP = {
    '<0xE0><0xB2><0x94>': 'ಔ',
    '<0xE0><0xB2><0x8A>': 'ಊ',
    '<0xE0><0xB2><0x8E>': 'ಎ',
    '<0xE0><0xB2><0x90>': 'ಐ',
    '<0xE0><0xB2><0xA2>': 'ಢ',
    '<0xE0><0xB2><0x9D>': 'ಝ',
    '<0xE0><0xB2><0x8B>': 'ಋ',
    '<0x2E>': '.',
}

# --- Helper Functions ---

def fix_bytecodes(text):
    """Replace bytecodes with proper Kannada characters"""
    corrected = text
    for bytecode, kannada_char in BYTECODE_MAP.items():
        corrected = corrected.replace(bytecode, kannada_char)
    return corrected

def split_text_into_chunks(text, max_chars=100):
    """Split text into chunks of approximately max_chars, splitting at sentence or word boundaries"""
    if len(text) <= max_chars:
        return [text]
    
    chunks = []
    # Sentence delimiters for Kannada and English
    sentence_delimiters = ['।', '.', '!', '?', '\n']
    
    current_chunk = ""
    sentences = []
    
    # First, try to split by sentences
    temp = text
    for delimiter in sentence_delimiters:
        temp = temp.replace(delimiter, delimiter + '<SPLIT>')
    
    parts = temp.split('<SPLIT>')
    
    for part in parts:
        part = part.strip()
        if not part:
            continue
            
        # If adding this part would exceed max_chars, save current chunk and start new one
        if current_chunk and len(current_chunk) + len(part) + 1 > max_chars:
            chunks.append(current_chunk.strip())
            current_chunk = part
        else:
            if current_chunk:
                current_chunk += " " + part
            else:
                current_chunk = part
        
        # If current part itself is too long, split by words
        if len(current_chunk) > max_chars:
            words = current_chunk.split()
            temp_chunk = ""
            for word in words:
                if len(temp_chunk) + len(word) + 1 <= max_chars:
                    temp_chunk += (" " if temp_chunk else "") + word
                else:
                    if temp_chunk:
                        chunks.append(temp_chunk.strip())
                    temp_chunk = word
            current_chunk = temp_chunk
    
    if current_chunk:
        chunks.append(current_chunk.strip())
    
    return chunks if chunks else [text]

def stitch_audio_bytes(audio_chunks_list):
    """Stitch multiple WAV audio byte arrays together by combining audio data and fixing header"""
    if not audio_chunks_list:
        return b''
    if len(audio_chunks_list) == 1:
        return audio_chunks_list[0]
    
    # Parse WAV header from first chunk to get format info
    # WAV header structure: RIFF (4), filesize-8 (4), WAVE (4), fmt (4), fmt_size (4), format_data (16), data (4), data_size (4)
    first_chunk = audio_chunks_list[0]
    
    # Extract header from first chunk (typically 44 bytes for standard WAV)
    if len(first_chunk) < 44:
        # If too short, just concatenate
        return b''.join(audio_chunks_list)
    
    # Find the "data" chunk in the first WAV file
    data_offset = first_chunk.find(b'data')
    if data_offset == -1:
        # No data chunk found, fallback to simple concat
        return b''.join(audio_chunks_list)
    
    # The data chunk header is "data" (4 bytes) + size (4 bytes)
    # Audio data starts after these 8 bytes
    audio_data_start = data_offset + 8
    
    # Collect all audio data (skip headers from each chunk)
    all_audio_data = []
    for i, chunk in enumerate(audio_chunks_list):
        if i == 0:
            # For first chunk, include from audio_data_start
            all_audio_data.append(chunk[audio_data_start:])
        else:
            # For subsequent chunks, find and skip their headers too
            chunk_data_offset = chunk.find(b'data')
            if chunk_data_offset != -1:
                chunk_audio_start = chunk_data_offset + 8
                all_audio_data.append(chunk[chunk_audio_start:])
            else:
                # If can't find data marker, skip first 44 bytes as fallback
                all_audio_data.append(chunk[44:] if len(chunk) > 44 else chunk)
    
    # Combine all audio data
    combined_audio_data = b''.join(all_audio_data)
    
    # Create new WAV file with corrected header
    # Take header from first chunk up to the data size field
    header = bytearray(first_chunk[:audio_data_start])
    
    # Update the data chunk size (4 bytes before audio data starts)
    new_data_size = len(combined_audio_data)
    header[audio_data_start - 4:audio_data_start] = new_data_size.to_bytes(4, 'little')
    
    # Update the file size in RIFF header (at bytes 4-8)
    # RIFF chunk size = 4 (WAVE) + 8 (fmt) + 16 (fmt data) + 8 (data header) + data_size
    new_file_size = 36 + new_data_size  # 36 = header size before data
    header[4:8] = new_file_size.to_bytes(4, 'little')
    
    # Combine header and audio data
    return bytes(header) + combined_audio_data

def load_messages_from_json():
    """Load message history from JSON file"""
    try:
        if os.path.exists(MESSAGES_FILE):
            with open(MESSAGES_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        return []
    except Exception as e:
        st.error(f"Error loading messages: {e}")
        return []

def save_messages_to_json(messages):
    """Save complete message history to JSON file (atomic write)"""
    try:
        # Write to temp file first, then rename (atomic operation)
        temp_file = MESSAGES_FILE + ".tmp"
        with open(temp_file, 'w', encoding='utf-8') as f:
            json.dump(messages, f, ensure_ascii=False, indent=2)
        os.replace(temp_file, MESSAGES_FILE)
    except Exception as e:
        st.error(f"Error saving messages: {e}")

def append_message_to_json(message):
    """Append a single message to the JSON file"""
    messages = load_messages_from_json()
    messages.append(message)
    save_messages_to_json(messages)

def clear_all_messages():
    """Clear all messages and delete the JSON file"""
    try:
        if os.path.exists(MESSAGES_FILE):
            os.remove(MESSAGES_FILE)
        return True
    except Exception as e:
        st.error(f"Error clearing messages: {e}")
        return False

def load_context():
    """Loads the knowledge base from JSON"""
    try:
        with open(CONTEXT_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        st.error(f"Context file '{CONTEXT_FILE}' not found.")
        return {}
    except Exception as e:
        st.error(f"Error loading context: {e}")
        return {}

def save_audio_to_file(audio_bytes, message_id):
    """Save audio bytes to a file and return the file path"""
    filename = f"response_{message_id}.wav"
    filepath = AUDIO_STORAGE_DIR / filename
    
    with open(filepath, 'wb') as f:
        f.write(audio_bytes)
        f.flush()
        os.fsync(f.fileno())
    
    return str(filepath)

def get_session_audio_files():
    """Get list of audio files created in this session"""
    if "session_audio_files" not in st.session_state:
        st.session_state.session_audio_files = []
    return st.session_state.session_audio_files

def track_audio_file(filepath):
    """Track an audio file for this session"""
    if "session_audio_files" not in st.session_state:
        st.session_state.session_audio_files = []
    st.session_state.session_audio_files.append(filepath)

def cleanup_session_audio_files():
    """Delete all audio files created in this session"""
    audio_files = get_session_audio_files()
    deleted_count = 0
    for filepath in audio_files:
        try:
            if os.path.exists(filepath):
                os.remove(filepath)
                deleted_count += 1
        except Exception as e:
            print(f"Could not delete {filepath}: {e}")
    
    if deleted_count > 0:
        print(f"Cleaned up {deleted_count} audio files from session")
    
    st.session_state.session_audio_files = []

def get_genai_client(sa_index: int = 1):
    sa_key = "SA_1" if sa_index % 2 == 0 else "SA_2"
    return SA_CLIENTS[sa_key]

def generate_and_parse_response(genai_client, messages, metadata_string):
    """Generate content from Gemini and parse Kannada JSON response"""
    response = genai_client.models.generate_content(
        model="gemini-2.5-flash",
        contents=messages,
        config=GenerateContentConfig(
            system_instruction=f"{MASTER_INSTRUCTIONS}\n\n### Additional User Information: {metadata_string}.",
            temperature=0.25,
            response_mime_type="application/json",
            thinking_config={"thinking_budget": 2048},
        ),
    )

    if not response or not response.candidates:
        return response, None

    candidate = response.candidates[0]
    if not candidate.content or not candidate.content.parts:
        return response, None

    raw_text = candidate.content.parts[0].text
    if not raw_text:
        return response, None

    try:
        data = json.loads(raw_text)
        result = {
            "answer": data.get("answer", ""),
            "source_reference": data.get("source_reference", "N/A")
        }
        return response, result
    except json.JSONDecodeError:
        return response, {
            "answer": raw_text,
            "source_reference": "N/A"
        }

# --- Main Application ---

def main():
    st.set_page_config(page_title="Gov Voice Assistant", page_icon="🏛️")
    st.title("🏛️ Government Voice Assistant")

    # Register cleanup on exit
    atexit.register(cleanup_session_audio_files)

    # Sidebar for controls
    with st.sidebar:
        st.header("Settings")
        language = st.selectbox(
            "Speech Language:",
            ["kannada", "hindi", "english"],
            index=0
        )
        
        # Debug mode toggle
        debug_mode = st.checkbox("🐛 Debug Mode", value=False)
        
        # Load Context
        context_data = load_context()
        context_str = json.dumps(context_data)
        with st.expander("View Active Context"):
            st.json(context_data)
        
        st.divider()
        
        # Clear chat button
        if st.button("🗑️ Clear Chat History", type="secondary", use_container_width=True):
            if clear_all_messages():
                cleanup_session_audio_files()
                st.success("Chat history cleared!")
                st.rerun()
        
        # Debug info
        if debug_mode:
            st.divider()
            st.subheader("🔍 Debug Info")
            st.write(f"**TTS API:** `{TTS_API_URL}`")
            st.write(f"**Messages file:** `{MESSAGES_FILE}`")
            st.write(f"**Audio dir:** `{AUDIO_STORAGE_DIR}`")
            
            # Show session audio files
            session_files = get_session_audio_files()
            st.write(f"**Session audio files:** {len(session_files)}")
            if session_files:
                for f in session_files[-3:]:  # Show last 3
                    exists = "✅" if os.path.exists(f) else "❌"
                    st.caption(f"{exists} {Path(f).name}")

    # Initialize session state for temporary audio storage
    if "temp_audio" not in st.session_state:
        st.session_state.temp_audio = None
    if "temp_audio_filename" not in st.session_state:
        st.session_state.temp_audio_filename = "recording.wav"
    if "processing" not in st.session_state:
        st.session_state.processing = False

    # Load and display all messages from JSON
    messages = load_messages_from_json()
    
    for msg in messages:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])
            
            # Display audio for assistant messages
            if msg["role"] == "assistant" and msg.get("audio_file"):
                audio_path = msg["audio_file"]
                if os.path.exists(audio_path):
                    # Use sample_rate if available for proper playback
                    sample_rate = msg.get("sample_rate")
                    if sample_rate:
                        st.audio(audio_path, sample_rate=sample_rate)
                    else:
                        st.audio(audio_path)
                else:
                    st.caption("_Audio file not found_")
            
            # Show TTS debug info in debug mode
            if debug_mode and msg["role"] == "assistant" and msg.get("tts_debug"):
                with st.expander("🐛 TTS Debug Info"):
                    st.json(msg["tts_debug"])

    # --- Input Section ---
    st.write("---")
    
    # Recording interface
    try:
        from streamlit_mic_recorder import mic_recorder
        
        col1, col2 = st.columns([1, 1])
        
        with col1:
            st.write("🎙️ **Record Audio:**")
            recorded_audio = mic_recorder(
                start_prompt="🔴 Start Recording",
                stop_prompt="⏹️ Stop Recording",
                key="voice_recorder"
            )
            
            # Store recorded audio in session state
            if recorded_audio and recorded_audio.get('bytes'):
                st.session_state.temp_audio = recorded_audio['bytes']
                st.session_state.temp_audio_filename = "recording.wav"
        
        with col2:
            st.write("📁 **Or Upload Audio:**")
            uploaded_file = st.file_uploader(
                "Upload audio file",
                type=["wav", "mp3", "ogg"],
                label_visibility="collapsed",
                key="audio_uploader"
            )
            
            # Store uploaded audio in session state
            if uploaded_file:
                st.session_state.temp_audio = uploaded_file.read()
                st.session_state.temp_audio_filename = uploaded_file.name

    except ImportError:
        st.error("⚠️ Please install streamlit-mic-recorder: `pip install streamlit-mic-recorder`")
        st.stop()

    # Show status and send button if audio is ready
    if st.session_state.temp_audio and not st.session_state.processing:
        st.success("✅ Audio ready to send!")
        
        col_send, col_cancel = st.columns([3, 1])
        with col_send:
            send_button = st.button("📤 Send Message", type="primary", use_container_width=True)
        with col_cancel:
            if st.button("🗑️ Cancel", use_container_width=True):
                st.session_state.temp_audio = None
                st.session_state.temp_audio_filename = "recording.wav"
                st.rerun()
        
        if send_button:
            st.session_state.processing = True
            
            with st.status("Processing your request...", expanded=True) as status:
                
                # 1. STT - Transcribe audio
                status.write("👂 Transcribing audio...")
                transcribed_text = ""
                
                try:
                    files = {
                        'file': (
                            st.session_state.temp_audio_filename,
                            io.BytesIO(st.session_state.temp_audio),
                            'audio/wav'
                        )
                    }
                    data = {'language': language}
                    
                    stt_response = requests.post(STT_API_URL, files=files, data=data, timeout=60)
                    
                    if stt_response.status_code == 200:
                        result = stt_response.json()
                        raw_text = (
                            result.get('text') or 
                            result.get('transcription') or 
                            result.get('transcript') or 
                            ''
                        )
                        transcribed_text = fix_bytecodes(raw_text)
                        status.write(f"✅ Transcribed: {transcribed_text}")
                    else:
                        status.update(label="❌ STT Error", state="error")
                        st.error(f"STT Error: {stt_response.text}")
                        st.session_state.processing = False
                        st.stop()
                        
                except Exception as e:
                    status.update(label="❌ STT Connection Error", state="error")
                    st.error(f"STT Error: {e}")
                    st.session_state.processing = False
                    st.stop()

                if not transcribed_text:
                    st.warning("No speech detected in audio.")
                    st.session_state.processing = False
                    st.session_state.temp_audio = None
                    st.stop()

                # Save user message to JSON
                user_message = {
                    "id": f"msg_{int(time.time() * 1000)}",
                    "role": "user",
                    "content": transcribed_text,
                    "timestamp": datetime.now().isoformat()
                }
                append_message_to_json(user_message)
                status.write("💾 User message saved")

                # 2. Gemini - Generate response
                status.write("🧠 Generating response...")
                
                # Prepare conversation history for Gemini
                all_messages = load_messages_from_json()
                gemini_history = []
                for msg in all_messages:
                    role = "user" if msg["role"] == "user" else "model"
                    gemini_history.append({"role": role, "parts": [{"text": msg["content"]}]})
                
                client = get_genai_client(sa_index=1)
                
                raw_response, response_json = generate_and_parse_response(
                    client, 
                    gemini_history, 
                    context_str
                )

                # Extract text response
                final_response_text = ""
                if response_json:
                    if "response" in response_json:
                        final_response_text = response_json["response"]
                    elif "answer" in response_json:
                        final_response_text = response_json["answer"]
                    else:
                        final_response_text = str(response_json)
                else:
                    final_response_text = "Sorry, I couldn't generate a valid response."

                status.write("✅ Response generated")

                # 3. TTS - Generate audio
                status.write("🔊 Generating audio response...")
                final_response_text = fix_bytecodes(final_response_text) 

                status.write(f"📝 Text to convert (length: {len(final_response_text)} chars)")
                audio_filepath = None
                
                # TTS debug metadata to store in JSON
                tts_metadata = {
                    "tts_attempted": True,
                    "tts_api_url": TTS_API_URL,
                    "text_length": len(final_response_text),
                    "timestamp": datetime.now().isoformat(),
                    "payload": final_response_text
                }
                
                try:
                    # Split text into chunks if too long
                    text_chunks = split_text_into_chunks(final_response_text, max_chars=100)
                    tts_metadata["num_chunks"] = len(text_chunks)
                    tts_metadata["chunks"] = text_chunks
                    
                    if len(text_chunks) > 1:
                        status.write(f"✂️ Split into {len(text_chunks)} chunks for TTS")
                    
                    audio_chunks = []
                    sample_rate = 22050  # Default sample rate
                    
                    # Process each chunk
                    for i, chunk in enumerate(text_chunks):
                        chunk_status = f"📡 Chunk {i+1}/{len(text_chunks)}: Calling TTS API ({len(chunk)} chars)"
                        status.write(chunk_status)
                        
                        tts_response = requests.post(
                            TTS_API_URL, 
                            json={"text": chunk}, 
                            timeout=60
                        )
                        
                        if i == 0:  # Store metadata from first chunk
                            tts_metadata["status_code"] = tts_response.status_code
                            status.write(f"📥 TTS Response Status: {tts_response.status_code}")
                        
                        if tts_response.status_code == 200:
                            try:
                                tts_result = tts_response.json()
                                if i == 0:
                                    tts_metadata["response_keys"] = list(tts_result.keys())
                                    status.write(f"🔍 TTS Result Keys: {tts_metadata['response_keys']}")
                            except Exception as json_err:
                                tts_metadata["json_parse_error"] = str(json_err)
                                tts_metadata["raw_response"] = tts_response.text[:500]
                                status.write(f"❌ Failed to parse TTS JSON: {json_err}")
                                raise
                            
                            audio_b64 = tts_result.get("audio_base64")
                            chunk_sample_rate = tts_result.get("sample_rate", 22050)
                            if i == 0:
                                sample_rate = chunk_sample_rate
                            
                            if audio_b64:
                                if i == 0:
                                    tts_metadata["base64_length"] = len(audio_b64)
                                    tts_metadata["sample_rate"] = sample_rate
                                    status.write(f"📦 Base64 audio length: {len(audio_b64)} chars")
                                    status.write(f"🎵 Sample rate: {sample_rate} Hz")
                                
                                try:
                                    audio_bytes = base64.b64decode(audio_b64)
                                    audio_chunks.append(audio_bytes)
                                    status.write(f"✅ Chunk {i+1} decoded: {len(audio_bytes)} bytes")
                                except Exception as decode_err:
                                    tts_metadata["decode_error"] = str(decode_err)
                                    status.write(f"❌ Base64 decode error: {decode_err}")
                                    raise
                            else:
                                tts_metadata["error"] = f"Chunk {i+1} missing 'audio_base64' field"
                                status.write(f"⚠️ {tts_metadata['error']}")
                                break
                        else:
                            tts_metadata["error"] = f"TTS API returned status {tts_response.status_code} for chunk {i+1}"
                            try:
                                error_detail = tts_response.text[:500]
                                tts_metadata["error_response"] = error_detail
                                status.write(f"📄 Error response: {error_detail}")
                            except:
                                pass
                            status.write(f"❌ {tts_metadata['error']}")
                            break
                    
                    # Stitch audio chunks together
                    if audio_chunks:
                        if len(audio_chunks) > 1:
                            status.write(f"🔗 Stitching {len(audio_chunks)} audio chunks...")
                        
                        final_audio_bytes = stitch_audio_bytes(audio_chunks)
                        tts_metadata["decoded_bytes"] = len(final_audio_bytes)
                        tts_metadata["stitched_chunks"] = len(audio_chunks)
                        status.write(f"🎵 Final audio size: {len(final_audio_bytes)} bytes")
                        
                        if len(final_audio_bytes) > 0:
                            # Generate unique message ID
                            message_id = f"msg_{int(time.time() * 1000)}"
                            tts_metadata["message_id"] = message_id
                            
                            # Save audio to file
                            audio_filepath = save_audio_to_file(final_audio_bytes, message_id)
                            tts_metadata["audio_filepath"] = audio_filepath
                            status.write(f"💾 Audio file saved: {audio_filepath}")
                            
                            # Verify file exists and is readable
                            if os.path.exists(audio_filepath):
                                file_size = os.path.getsize(audio_filepath)
                                tts_metadata["file_size_on_disk"] = file_size
                                tts_metadata["file_exists"] = True
                                status.write(f"✅ Verified file on disk: {file_size} bytes")
                                
                                # Track this audio file for cleanup
                                track_audio_file(audio_filepath)
                                tts_metadata["success"] = True
                            else:
                                tts_metadata["file_exists"] = False
                                tts_metadata["error"] = f"File not found after save: {audio_filepath}"
                                status.write(f"❌ ERROR: {tts_metadata['error']}")
                                audio_filepath = None
                        else:
                            tts_metadata["error"] = "TTS returned empty audio (0 bytes after decode)"
                            status.write(f"⚠️ {tts_metadata['error']}")
                    else:
                        tts_metadata["error"] = "No audio chunks were successfully generated"
                        status.write(f"⚠️ {tts_metadata['error']}")
                        
                except requests.exceptions.Timeout:
                    tts_metadata["error"] = "TTS request timed out (60s)"
                    status.write(f"❌ {tts_metadata['error']}")
                except requests.exceptions.ConnectionError as conn_err:
                    tts_metadata["error"] = f"Cannot connect to TTS API: {conn_err}"
                    status.write(f"❌ {tts_metadata['error']}")
                    status.write(f"🔗 Check if server is running at: {TTS_API_URL}")
                except Exception as e:
                    tts_metadata["error"] = f"{type(e).__name__}: {str(e)}"
                    import traceback
                    tts_metadata["traceback"] = traceback.format_exc()
                    status.write(f"❌ TTS Failed: {tts_metadata['error']}")
                    status.write(f"📋 Traceback: {tts_metadata['traceback']}")

                # Save assistant message to JSON
                assistant_message = {
                    "id": f"msg_{int(time.time() * 1000) + 1}",
                    "role": "assistant",
                    "content": final_response_text,
                    "timestamp": datetime.now().isoformat(),
                    "tts_debug": tts_metadata  # Store all TTS debug info
                }
                
                if audio_filepath and os.path.exists(audio_filepath):
                    assistant_message["audio_file"] = audio_filepath
                    # Store sample rate if available for proper playback
                    if "sample_rate" in tts_metadata:
                        assistant_message["sample_rate"] = tts_metadata["sample_rate"]
                
                append_message_to_json(assistant_message)
                status.write("💾 Assistant message saved")
                
                status.update(label="✅ Complete!", state="complete", expanded=False)
            
            # Clear temporary audio and reset state
            st.session_state.temp_audio = None
            st.session_state.temp_audio_filename = "recording.wav"
            st.session_state.processing = False
            
            # Rerun to display new messages
            time.sleep(0.2)  # Small delay to ensure JSON is written
            st.rerun()
    
    elif st.session_state.processing:
        st.info("⏳ Processing your message...")
    else:
        st.info("🎤 Record or upload audio to start")

if __name__ == "__main__":
    main()