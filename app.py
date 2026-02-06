import streamlit as st

# Page config - must be first Streamlit command
st.set_page_config(
    page_title="AI Tools Suite",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Initialize SSH tunnels before anything else
from ssh_tunnel_manager import initialize_tunnels

# Start SSH tunnels (only runs once)
if 'tunnels_initialized' not in st.session_state:
    with st.spinner("🔒 Establishing secure connections..."):
        initialize_tunnels()
        st.session_state.tunnels_initialized = True

# Hide Streamlit's default header, menu, and footer
st.markdown("""
    <style>
    #MainMenu {visibility: hidden;}
    header {visibility: hidden;}
    footer {visibility: hidden;}
    .stDeployButton {display: none;}
    
    /* Hide file viewer/browser in sidebar */
    [data-testid="stSidebarNav"] {display: none;}
    </style>
""", unsafe_allow_html=True)

# Import page modules
from pages import home, ocr, stt, translation, tts

# Sidebar navigation
st.sidebar.title("🤖 AI Tools Suite")
st.sidebar.markdown("---")

# Navigation menu
page = st.sidebar.radio(
    "Select a tool:",
    ["🏠 Home", "📝 OCR", "🎙️ Voice Bot", "🌍 Translation", "🔊 Text-to-Speech"],
    index=0
)

st.sidebar.markdown("---")
st.sidebar.markdown(
    """
    <div style='text-align: center; color: #666; font-size: 0.8em;'>
    <p>AI Tools Suite v1.0</p>
    <p>Select a tool from above to get started</p>
    </div>
    """,
    unsafe_allow_html=True
)

# Route to appropriate page
if page == "🏠 Home":
    home.show()
elif page == "📝 OCR":
    ocr.show()
elif page == "🎙️ Voice Bot":
    stt.show()
elif page == "🌍 Translation":
    translation.show()
elif page == "🔊 Text-to-Speech":
    tts.show()