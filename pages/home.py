import streamlit as st

def show():
    """Display the home page with welcome message and tool overview"""
    
    # Simple welcome message
    st.markdown(
        """
        <div style='text-align: center; padding: 1rem 0;'>
            <p style='font-size: 1.1rem; color: #666;'>
                Your all-in-one platform for AI-powered text, speech, and vision tasks
            </p>
        </div>
        """,
        unsafe_allow_html=True
    )
    
    # Tools overview
    st.header("Available Tools")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown(
            """
            ### 📝 OCR (Optical Character Recognition)
            Extract text from images in multiple languages including Kannada, Hindi, and English.
            
            **Features:**
            - Multi-language support
            - High accuracy text extraction
            - Easy image upload
            
            ---
            
            ### 🎙️ Voice Bot
            Interactive voice-based chatbot with speech recognition and AI responses.
            
            **Features:**
            - Voice input/output
            - Gemini AI integration
            - Chat history
            """
        )
    
    with col2:
        st.markdown(
            """
            ### 🌍 Translation
            Translate English text to Kannada with advanced batching for long documents.
            
            **Features:**
            - Batch processing
            - Handles long texts
            - High-quality translation
            
            ---
            
            ### 🔊 Text-to-Speech
            Convert Kannada text to natural-sounding speech.
            
            **Features:**
            - Natural voice synthesis
            - Audio download
            - Real-time generation
            """
        )
    
    st.markdown("---")
    
    # Getting started section
    st.header("🚀 Getting Started")
    
    st.markdown(
        """
        1. **Select a tool** from the sidebar on the left
        2. **Follow the instructions** for each specific tool
        3. **Enjoy** the AI-powered capabilities!
        
        ### 📋 Prerequisites
        
        Make sure you have the following backend services running:
        
        - **OCR Service**: `http://localhost:8004/infer`
        - **TTS Service**: `http://localhost:8002/tts`
        - **Translation Service**: `http://localhost:8003/translate`
        - **Gemini API Key**: Required for Voice Bot (enter in settings)
        
        ### 💡 Tips
        
        - Start with smaller files/texts to test each service
        - Check that backend services are running before using the tools
        - For Voice Bot, configure your API key in the sidebar settings
        """
    )
    
    st.markdown("---")
    
    # Footer
    st.markdown(
        """
        <div style='text-align: center; color: #666; padding: 2rem 0;'>
            <p>Built with ❤️ using Streamlit and various AI models</p>
            <p style='font-size: 0.9rem;'>Select a tool from the sidebar to begin</p>
        </div>
        """,
        unsafe_allow_html=True
    )