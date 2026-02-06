# 🤖 AI Tools Suite

A unified Streamlit application providing multiple AI-powered tools for text, speech, and vision tasks.

## 🌟 Features

### 📝 OCR (Optical Character Recognition)
- Extract text from images in multiple languages (Kannada, Hindi, English)
- Support for common image formats (PNG, JPG, JPEG)
- High accuracy text extraction

### 🎙️ Voice Bot
- Interactive voice-based chatbot
- Google Gemini AI integration
- Speech-to-text and text-to-speech capabilities
- Persistent chat history

### 🌍 Translation
- English to Kannada translation
- Batch processing for long documents
- Optimized for handling large texts efficiently

### 🔊 Text-to-Speech
- Convert Kannada text to natural speech
- Audio preview and download
- High-quality voice synthesis

## 🚀 Installation

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd ai-tools-suite
   ```

2. **Create a virtual environment** (recommended)
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

## ⚙️ Configuration

### SSH Tunnels (Required)

This app requires SSH tunnels to backend services. Configure `ssh_tunnel_manager.py`:

```python
# Update these values in ssh_tunnel_manager.py
JUMP_HOST = "ubuntu@your_jump_host_ip"
TARGET_HOST = "neurodx@your_target_host_ip"

# Option 1: Use SSH keys (recommended)
JUMP_PASSWORD = ""
TARGET_PASSWORD = ""

# Option 2: Use passwords (requires 'expect' installed)
JUMP_PASSWORD = "your_jump_password"
TARGET_PASSWORD = "your_target_password"
```

**For password-based authentication**, install expect:
```bash
# Ubuntu/Debian
sudo apt-get install expect

# macOS
brew install expect
```

The app will automatically establish tunnels for ports 8000-8004 when it starts.

### Backend Services

The SSH tunnels connect to these services on the remote host:
- **Port 8000**: General service
- **Port 8001**: STT service  
- **Port 8002**: TTS service
- **Port 8003**: Translation service
- **Port 8004**: OCR service

### API Keys

For the Voice Bot feature, you'll need:
- **Google Gemini API Key**: Get it from [Google AI Studio](https://makersuite.google.com/app/apikey)

Enter the API key in the Voice Bot settings sidebar when using the app.

## 🎯 Usage

1. **Start the application**
   ```bash
   streamlit run app.py
   ```

2. **Access the web interface**
   - Open your browser and navigate to `http://localhost:8501`

3. **Select a tool**
   - Use the sidebar navigation to switch between different tools
   - Follow the on-screen instructions for each tool

## 📁 Project Structure

```
ai-tools-suite/
├── app.py                 # Main application entry point
├── pages/                 # Page modules
│   ├── __init__.py
│   ├── home.py           # Home/landing page
│   ├── ocr.py            # OCR interface
│   ├── stt.py            # Voice bot interface
│   ├── translation.py    # Translation interface
│   └── tts.py            # Text-to-speech interface
├── requirements.txt       # Python dependencies
├── .gitignore            # Git ignore rules
└── README.md             # This file
```

## 🔧 Troubleshooting

### Connection Errors
- Ensure all backend services are running on the correct ports
- Check firewall settings if services can't be reached

### Voice Bot Not Working
- Verify your Gemini API key is correct
- Check your internet connection
- Ensure the API key has necessary permissions

### Audio Issues
- Make sure your browser has microphone permissions
- Check system audio settings for TTS output

## 🛠️ Development

To extend or modify the application:

1. Each tool is modular in the `pages/` directory
2. Add new tools by creating a new module in `pages/`
3. Update `app.py` to include the new tool in navigation

## 📝 Requirements

- Python 3.8+
- Streamlit 1.28.0+
- Active internet connection for Voice Bot
- Running backend services for OCR, TTS, and Translation

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## 📄 License

This project is open source and available under the MIT License.

## 🆘 Support

For issues or questions:
- Check the troubleshooting section above
- Review backend service logs
- Ensure all dependencies are properly installed

---

Built with ❤️ using Streamlit and various AI models