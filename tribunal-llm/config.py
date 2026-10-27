# config.py
from pathlib import Path
from dotenv import load_dotenv
import os

load_dotenv()

BASE_DIR = Path(__file__).parent
DATA_DIR = BASE_DIR / "data"
CHROMA_DIR = BASE_DIR / "chroma_db"
CODIGO_DO_TRABALHO_PATH = DATA_DIR / "codigo_do_trabalho.txt"

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
GROQ_API_KEY = os.getenv("GROQ_API_KEY")

GEMINI_MODEL = "gemini-3.8-flash"          
GROQ_MODEL = "openai/gpt-oss-120b"     
EMBEDDING_MODEL = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"

CHROMA_COLLECTION = "codigo_do_trabalho_collection"