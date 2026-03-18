import streamlit as st
import requests
import json
import base64
import tempfile
import os
import time
from datetime import datetime
from config import Config

# ==========================================
# PAGE CONFIG
# ==========================================
st.set_page_config(
    page_title="Voice AI Chat - Continuous Conversation",
    page_icon="🎤",
    layout="wide"
)

# ==========================================
# LOAD CONFIGURATION
# ==========================================
config_ok, config_msg = Config.validate()
if not config_ok:
    st.error(f"⚠️ {config_msg}")
    st.info("Please create a .env file with your API credentials")
    st.code("""
PIPER_API_URL=your-piper-api-url
PIPER_PASSWORD=your-password
    """)
    st.stop()

# ==========================================
# SESSION STATE INITIALIZATION
# ==========================================
if "messages" not in st.session_state:
    st.session_state.messages = [
        {"role": "assistant", "content": "Hello! I'm your voice-enabled AI assistant. We can talk continuously - just keep asking questions!"}
    ]

if "conversation_active" not in st.session_state:
    st.session_state.conversation_active = True

if "last_audio" not in st.session_state:
    st.session_state.last_audio = None

# ==========================================
# FUNCTIONS
# ==========================================

def call_llama(prompt, conversation_history=None):
    """Call local Llama model via Ollama with conversation context"""
    try:
        # Build prompt with conversation history for continuity
        if conversation_history and len(conversation_history) > 1:
            # Take last 4 messages for context (2 exchanges)
            recent = conversation_history[-4:]
            context = "\n".join([f"{msg['role']}: {msg['content']}" for msg in recent])
            full_prompt = f"{context}\nuser: {prompt}\nassistant:"
        else:
            full_prompt = prompt
        
        payload = {
            "model": Config.OLLAMA_MODEL,
            "prompt": full_prompt,
            "stream": False,
            "options": {
                "temperature": 0.7,
                "max_tokens": 500
            }
        }
        
        response = requests.post(Config.OLLAMA_URL, json=payload, timeout=30)
        
        if response.status_code == 200:
            return response.json().get("response", "Sorry, I couldn't generate a response.")
        else:
            return f"Error: {response.status_code}"
            
    except requests.exceptions.ConnectionError:
        return "❌ Cannot connect to Ollama. Make sure it's running with 'ollama serve'"
    except requests.exceptions.Timeout:
        return "❌ Request timed out"
    except Exception as e:
        return f"❌ Error: {str(e)}"

def text_to_speech(text):
    """Convert text to speech using Piper API"""
    try:
        headers = {
            "Authorization": Config.PIPER_PASSWORD,
            "Content-Type": "application/json"
        }
        
        payload = {
            "text": text,
            "voice": "en_US-amy-medium",
            "speed": 1.0
        }
        
        response = requests.post(
            Config.PIPER_API_URL, 
            json=payload, 
            headers=headers,
            timeout=15
        )
        
        if response.status_code == 200:
            # Save to temp file
            with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as tmp:
                tmp.write(response.content)
                return tmp.name
        else:
            st.error(f"TTS API Error: {response.status_code}")
            return None
            
    except Exception as e:
        st.error(f"TTS Error: {str(e)}")
        return None

def check_ollama():
    """Check if Ollama is running"""
    try:
        response = requests.get("http://localhost:11434/api/tags", timeout=2)
        return response.status_code == 200
    except:
        return False

def check_piper():
    """Check if Piper API is accessible"""
    try:
        health_url = Config.PIPER_API_URL.replace("/v1/tts", "/health")
        response = requests.get(health_url, headers={"Authorization": Config.PIPER_PASSWORD}, timeout=2)
        return response.status_code == 200
    except:
        return False

# ==========================================
# SIDEBAR
# ==========================================
with st.sidebar:
    st.title("🎤 Voice AI Chat")
    st.markdown("---")
    
    # Status indicators
    st.subheader("📊 System Status")
    
    col1, col2 = st.columns(2)
    with col1:
        if check_ollama():
            st.success("✅ Ollama")
        else:
            st.error("❌ Ollama")
    
    with col2:
        if check_piper():
            st.success("✅ Piper API")
        else:
            st.error("❌ Piper API")
    
    st.markdown("---")
    
    # Conversation controls
    st.subheader("💬 Conversation")
    
    if st.button("🔄 New Conversation", use_container_width=True):
        st.session_state.messages = [
            {"role": "assistant", "content": "Hello! I'm your voice-enabled AI assistant. Let's start a new conversation!"}
        ]
        st.session_state.last_audio = None
        st.rerun()
    
    if st.button("🗑️ Clear Chat", use_container_width=True):
        st.session_state.messages = []
        st.session_state.last_audio = None
        st.rerun()
    
    st.markdown("---")
    
    # Voice settings
    st.subheader("🎙️ Voice Settings")
    voice_option = st.selectbox(
        "Voice",
        ["en_US-amy-medium", "en_US-lessac-medium"],
        index=0
    )
    
    speed = st.slider("Speed", 0.8, 1.3, 1.0, 0.1)
    
    st.markdown("---")
    
    # Info
    st.info(f"🤖 Model: {Config.OLLAMA_MODEL}")
    st.caption("Continuous conversation - AI remembers context")

# ==========================================
# MAIN CHAT INTERFACE
# ==========================================
st.title("🎤 Voice AI Chat - Continuous Conversation")
st.caption("Ask anything - the AI remembers our conversation and speaks back!")

# Display chat messages
for i, message in enumerate(st.session_state.messages):
    with st.chat_message(message["role"]):
        st.write(message["content"])
        
        # Show audio player for last assistant message only (optional)
        if message["role"] == "assistant" and i == len(st.session_state.messages) - 1:
            if st.session_state.last_audio and os.path.exists(st.session_state.last_audio):
                with open(st.session_state.last_audio, "rb") as f:
                    st.audio(f.read(), format="audio/wav")

# Chat input
if prompt := st.chat_input("Type your message (keep the conversation going)..."):
    # Add user message
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.write(prompt)
    
    # Get AI response
    with st.chat_message("assistant"):
        with st.spinner("🤔 Thinking..."):
            # Pass conversation history for continuity
            response = call_llama(prompt, st.session_state.messages)
            
            st.write(response)
            
            # Generate speech
            with st.spinner("🔊 Speaking..."):
                audio_file = text_to_speech(response)
                
                if audio_file:
                    # Clean up old audio file
                    if st.session_state.last_audio and os.path.exists(st.session_state.last_audio):
                        try:
                            os.unlink(st.session_state.last_audio)
                        except:
                            pass
                    
                    # Play new audio
                    with open(audio_file, "rb") as f:
                        audio_bytes = f.read()
                    
                    st.audio(audio_bytes, format="audio/wav")
                    st.session_state.last_audio = audio_file
                else:
                    st.warning("⚠️ Could not generate speech, but response is above")
    
    # Save to session
    st.session_state.messages.append({"role": "assistant", "content": response})

# ==========================================
# CONTINUOUS CONVERSATION TIPS
# ==========================================
with st.expander("💡 Conversation Tips"):
    st.markdown("""
    ### How to have a continuous conversation:
    
    1. **Just keep typing** - The AI remembers our conversation
    2. **Ask follow-ups**: "Tell me more about that", "Why is that?"
    3. **Refer to previous messages**: "You just mentioned..."
    4. **Change topics anytime** - The AI adapts
    
    ### Examples:
    - "Tell me about Python"
    - "What are its main features?" (follow-up)
    - "Can you give me an example?" (another follow-up)
    - "Now tell me about JavaScript" (topic change)
    """)

# ==========================================
# FOOTER
# ==========================================
st.markdown("---")
st.caption("🚀 Powered by: Local Llama 3.2 + Piper TTS on Hugging Face | Continuous conversation with context memory")
