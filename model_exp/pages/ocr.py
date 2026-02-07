import streamlit as st
import requests
import base64
from PIL import Image
import io
import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
env_path = Path(__file__).parent.parent / '.env'
load_dotenv(env_path)

def show():
    """Display the OCR interface"""
    
    st.title("📝 OCR Text Extraction")
    
    # API endpoint
    NGROK_BASE = os.getenv("NGROK_BASE_URL", "https://your-ngrok-url.ngrok-free.app")
    API_URL = f"{NGROK_BASE}/ocr/infer"
    
    # Language selection
    language = st.selectbox(
        "Select language:",
        ["kannada", "hindi", "english"],
        index=0
    )
    
    # File uploader
    uploaded_file = st.file_uploader(
        "Upload an image:",
        type=["png", "jpg", "jpeg"],
        help="Upload an image containing text to extract"
    )
    
    # Display uploaded image
    if uploaded_file is not None:
        image = Image.open(uploaded_file)
        st.image(image, caption="Uploaded Image", use_container_width=True)
        
        # Process button
        if st.button("Extract Text", type="primary"):
            with st.spinner("Extracting text..."):
                try:
                    # Convert image to base64
                    img_byte_arr = io.BytesIO()
                    image.save(img_byte_arr, format=image.format or 'PNG')
                    img_byte_arr = img_byte_arr.getvalue()
                    image_b64 = base64.b64encode(img_byte_arr).decode('utf-8')
                    
                    # Prepare payload
                    payload = {
                        "image_b64": image_b64,
                        "prompt": "<image>",
                        "language": language,
                        "temperature": 0.0,
                        "max_tokens": 8192
                    }
                    
                    # Make API request
                    response = requests.post(API_URL, json=payload)
                    
                    if response.status_code == 200:
                        result = response.json()
                        
                        if result.get('success'):
                            st.success("✅ Text extracted successfully!")
                            
                            # Display processing time
                            processing_time = result.get('processing_time', 0)
                            st.info(f"⏱️ Processing time: {processing_time:.2f} seconds")
                            
                            # Display transcribed text
                            st.subheader("Extracted Text:")
                            transcribed_text = result.get('text', '')
                            st.markdown(f"### {transcribed_text}")
                            
                            # Code block for easy copying
                            st.code(transcribed_text, language=None)
                            
                        else:
                            error_msg = result.get('error', 'Unknown error')
                            st.error(f"❌ Error: {error_msg}")
                    else:
                        st.error(f"❌ API request failed: {response.status_code}")
                        st.error(response.text)
                        
                except requests.exceptions.ConnectionError:
                    st.error(f"❌ Failed to connect to {API_URL}. Is the server running?")
                except Exception as e:
                    st.error(f"❌ An error occurred: {str(e)}")
    else:
        st.info("👆 Upload an image to get started")
