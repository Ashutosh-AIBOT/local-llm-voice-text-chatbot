import streamlit as st
import subprocess
import tempfile
import os
import soundfile as sf
import numpy as np

# ==========================================
# LOCAL PIPER TTS - Runs entirely on your machine
# ==========================================

st.set_page_config(page_title="Local Piper TTS", page_icon="🔊")

st.title("🔊 Local Piper TTS")
st.write("100% local - no API calls, no internet needed!")

# Configuration - Update this path to where you downloaded the model
MODEL_PATH = os.path.expanduser("~/piper_models/en_US-amy-medium.onnx")

if not os.path.exists(MODEL_PATH):
    st.error(f"❌ Model not found at {MODEL_PATH}")
    st.info("Please download the model first using the commands above.")
    st.stop()

def text_to_speech_local(text, speed=1.0):
    """Generate speech using local Piper"""
    try:
        # Create temp file for output
        with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as tmp_file:
            output_path = tmp_file.name
        
        # Run piper command
        cmd = f'echo "{text}" | piper --model "{MODEL_PATH}" --output_file "{output_path}" --length_scale {1.0/speed}'
        
        process = subprocess.run(
            cmd,
            shell=True,
            capture_output=True,
            text=True,
            timeout=30
        )
        
        if process.returncode != 0:
            raise Exception(f"Piper failed: {process.stderr}")
        
        # Read audio
        audio, sr = sf.read(output_path)
        
        return audio, sr, output_path
        
    except Exception as e:
        if 'output_path' in locals() and os.path.exists(output_path):
            os.unlink(output_path)
        raise e

# Text input
text_input = st.text_area(
    "Enter text to speak:", 
    "Hello, this is running completely locally on my machine!",
    height=100
)

# Speed control
speed = st.slider("Speech speed:", 0.7, 1.5, 1.0, 0.1)

if st.button("🔊 Generate Speech", type="primary"):
    if not text_input.strip():
        st.warning("Please enter some text")
    else:
        with st.spinner("Generating audio locally..."):
            try:
                audio, sr, output_path = text_to_speech_local(text_input, speed)
                
                # Play audio
                st.audio(output_path)
                st.success("✅ Audio generated successfully!")
                
                # Download button
                with open(output_path, "rb") as f:
                    st.download_button(
                        label="📥 Download Audio",
                        data=f,
                        file_name="speech.wav",
                        mime="audio/wav"
                    )
                
                # Cleanup
                os.unlink(output_path)
                
            except Exception as e:
                st.error(f"❌ Failed: {str(e)}")

# Status
st.markdown("---")
col1, col2 = st.columns(2)
with col1:
    st.info(f"📁 Model: {os.path.basename(MODEL_PATH)}")
with col2:
    if os.path.exists(MODEL_PATH):
        st.success("✅ Model loaded locally")
    else:
        st.error("❌ Model not found")

st.caption("🚀 100% Local - No API calls, no internet needed!")