import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Server settings
HOST = os.getenv("HOST", "0.0.0.0")
PORT = int(os.getenv("PORT", 8000))

# Ollama settings
OLLAMA_API_HOST = os.getenv("OLLAMA_API_HOST", "http://localhost:11434")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "llama3-8b-instruct")

# prod 
# # MySQL Database settings
# DB_HOST = os.getenv("DB_HOST", "localhost")
# DB_PORT = int(os.getenv("DB_PORT", 3306))
# DB_USER = os.getenv("DB_USER", "root")
# DB_PASSWORD = os.getenv("DB_PASSWORD", "")
# DB_NAME = os.getenv("DB_NAME", "bms_db") 

# dev 
DB_HOST = os.getenv("DB_DEVELOPMENT", "localhost")
DB_PORT = int(os.getenv("DB_PORT", 3306))
DB_USER = os.getenv("DB_USER", "root")
DB_PASSWORD = os.getenv("DB_PASS_DEVELOPMENT", "")
DB_NAME = os.getenv("DB_NAME", "cmp") 