import streamlit as st

def show():
    """Display a minimalistic home page with clickable tool cards"""
    
    # Welcome header
    st.markdown(
        """
        <div style='text-align: center; padding: 2rem 0 3rem 0;'>
            <h1 style='margin-bottom: 0.5rem;'>AI Tools Suite</h1>
            <p style='font-size: 1.1rem; color: #888;'>
                Select a tool to get started
            </p>
        </div>
        """,
        unsafe_allow_html=True
    )
    
    # Tool cards in a 2x2 grid
    col1, col2 = st.columns(2, gap="large")
    
    with col1:
        # OCR Card
        st.markdown(
            """
            <div style='
                border: 2px solid #444;
                border-radius: 12px;
                padding: 2.5rem 1.5rem;
                text-align: center;
                height: 200px;
                display: flex;
                flex-direction: column;
                justify-content: center;
                background: transparent;
                margin-bottom: 2rem;
            '>
                <div style='font-size: 3rem; margin-bottom: 1rem;'>📝</div>
                <h3 style='margin: 0.5rem 0;'>OCR</h3>
                <p style='color: #888; font-size: 0.9rem; margin: 0;'>Extract text from images</p>
            </div>
            """,
            unsafe_allow_html=True
        )
        if st.button("Open OCR", key="ocr_btn", use_container_width=True):
            st.session_state.page = "📝 OCR"
            st.rerun()
        
        # Translation Card
        st.markdown(
            """
            <div style='
                border: 2px solid #444;
                border-radius: 12px;
                padding: 2.5rem 1.5rem;
                text-align: center;
                height: 200px;
                display: flex;
                flex-direction: column;
                justify-content: center;
                background: transparent;
                margin-top: 1rem;
            '>
                <div style='font-size: 3rem; margin-bottom: 1rem;'>🌍</div>
                <h3 style='margin: 0.5rem 0;'>Translation</h3>
                <p style='color: #888; font-size: 0.9rem; margin: 0;'>English to Kannada</p>
            </div>
            """,
            unsafe_allow_html=True
        )
        if st.button("Open Translation", key="translation_btn", use_container_width=True):
            st.session_state.page = "🌍 Translation"
            st.rerun()
    
    with col2:
        # Speech-to-Text Card
        st.markdown(
            """
            <div style='
                border: 2px solid #444;
                border-radius: 12px;
                padding: 2.5rem 1.5rem;
                text-align: center;
                height: 200px;
                display: flex;
                flex-direction: column;
                justify-content: center;
                background: transparent;
                margin-bottom: 2rem;
            '>
                <div style='font-size: 3rem; margin-bottom: 1rem;'>🎙️</div>
                <h3 style='margin: 0.5rem 0;'>Speech-to-Text</h3>
                <p style='color: #888; font-size: 0.9rem; margin: 0;'>AI-powered voice transcription</p>
            </div>
            """,
            unsafe_allow_html=True
        )
        if st.button("Open Speech-to-Text", key="voicebot_btn", use_container_width=True):
            st.session_state.page = "🎙️ Speech-to-Text"
            st.rerun()
        
        # Text-to-Speech Card
        st.markdown(
            """
            <div style='
                border: 2px solid #444;
                border-radius: 12px;
                padding: 2.5rem 1.5rem;
                text-align: center;
                height: 200px;
                display: flex;
                flex-direction: column;
                justify-content: center;
                background: transparent;
                margin-top: 1rem;
            '>
                <div style='font-size: 3rem; margin-bottom: 1rem;'>🔊</div>
                <h3 style='margin: 0.5rem 0;'>Text-to-Speech</h3>
                <p style='color: #888; font-size: 0.9rem; margin: 0;'>Convert text to voice</p>
            </div>
            """,
            unsafe_allow_html=True
        )
        if st.button("Open Text-to-Speech", key="tts_btn", use_container_width=True):
            st.session_state.page = "🔊 Text-to-Speech"
            st.rerun()