import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class Config:
    PIPER_API_URL = os.getenv("PIPER_API_URL")
    PIPER_PASSWORD = os.getenv("PIPER_PASSWORD")
    OLLAMA_URL = os.getenv("OLLAMA_URL", "http://localhost:11434/api/generate")
    OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "llama3.2:3b")
    
    @classmethod
    def validate(cls):
        missing = []
        if not cls.PIPER_API_URL:
            missing.append("PIPER_API_URL")
        if not cls.PIPER_PASSWORD:
            missing.append("PIPER_PASSWORD")
        
        if missing:
            return False, f"Missing config: {', '.join(missing)}"
        return True, "Config loaded"
