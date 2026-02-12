import streamlit as st

# Page config - must be first Streamlit command
st.set_page_config(
    page_title="AI Tools Suite",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Hide Streamlit's default menu, footer, deploy button, and default page navigation
st.markdown("""
    <style>
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    .stDeployButton {display: none;}
    section[data-testid="stSidebarNav"] {display: none !important;}
    [data-testid="stSidebarNav"] {display: none !important;}
    [data-testid="stSidebarNav"]::before {display: none !important;}
    [data-testid="stSidebarNav"]::after {display: none !important;}
    </style>
""", unsafe_allow_html=True)

# Import page modules
from pages import home, ocr, stt, translation, tts

# Initialize session state for page navigation
if 'page' not in st.session_state:
    st.session_state.page = "🏠 Home"

# Sidebar navigation
st.sidebar.title("🤖 AI Tools Suite")
st.sidebar.markdown("---")

# Navigation menu
page = st.sidebar.radio(
    "Select a tool:",
    ["🏠 Home", "📝 OCR", "🎙️ Speech-to-Text", "🌍 Translation", "🔊 Text-to-Speech"],
    index=["🏠 Home", "📝 OCR", "🎙️ Speech-to-Text", "🌍 Translation", "🔊 Text-to-Speech"].index(st.session_state.page) if st.session_state.page in ["🏠 Home", "📝 OCR", "🎙️ Speech-to-Text", "🌍 Translation", "🔊 Text-to-Speech"] else 0
)

# Update session state when sidebar selection changes
st.session_state.page = page

st.sidebar.markdown("---")
st.sidebar.markdown(
    """
    <div style='text-align: center; color: #666; font-size: 0.8em;'>
        <p>AI Tools Suite v1.0</p>
        <p>Select a tool to get started</p>
    </div>
    """,
    unsafe_allow_html=True
)

# Route to appropriate page
if st.session_state.page == "🏠 Home":
    home.show()
elif st.session_state.page == "📝 OCR":
    ocr.show()
elif st.session_state.page == "🎙️ Speech-to-Text":
    stt.show()
elif st.session_state.page == "🌍 Translation":
    translation.show()
elif st.session_state.page == "🔊 Text-to-Speech":
    tts.show()