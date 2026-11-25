# config.py
import os
from pathlib import Path
from dotenv import load_dotenv


# Silenciar telemetria do ChromaDB
os.environ.setdefault("ANONYMIZED_TELEMETRY", "False")

# 1. Definir BASE_DIR primeiro
BASE_DIR = Path(__file__).resolve().parent

# 2. Carregar o .env a partir da raiz do projeto 
load_dotenv(BASE_DIR / ".env")

# 3. Diretórios
DATA_DIR = BASE_DIR / "data"
CHROMA_DIR = BASE_DIR / "chroma_db"
CODIGO_DO_TRABALHO_PATH = DATA_DIR / "codigo_do_trabalho.txt"

# 4. API Keys
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY")


# 5. Modelos
GEMINI_MODEL = "gemini-flash-latest"          
GROQ_MODEL = "openai/gpt-oss-120b"
DEEPSEEK_MODEL = "deepseek-chat"      

# O novo modelo de embeddings que estamos a usar no GraphRAG
EMBEDDING_MODEL = "BAAI/bge-m3"

CHROMA_COLLECTION = "codigo_do_trabalho_collection"