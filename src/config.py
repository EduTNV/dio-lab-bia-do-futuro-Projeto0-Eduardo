import os
from dotenv import load_dotenv

load_dotenv()

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
DATA_DIR = os.getenv("DATA_DIR", "data/")

if not GEMINI_API_KEY:
    raise ValueError("ERRO CRÍTICO: A variável de ambiente 'GEMINI_API_KEY' não foi encontrada. Verifique se o arquivo .env está configurado corretamente na raiz do projeto com a chave da sua API do Gemini.")

BASE_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR_PATH = os.path.join(BASE_ROOT, DATA_DIR) if not os.path.isabs(DATA_DIR) else DATA_DIR
