import os
from dotenv import load_dotenv

load_dotenv()

# API Keys
# Try to get from environment variable, otherwise use the hardcoded one (as per user's current setup)
GROQ_API_KEY = os.getenv("GROQ_API_KEY")

# Flask Config
SECRET_KEY = os.getenv("SECRET_KEY", "your-secret-key-change-this-in-production")

# ChromaDB Config
CHROMA_DB_PATH = "./chroma_db"
EMBEDDING_MODEL = "all-MiniLM-L6-v2"
