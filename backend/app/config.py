import os

SECRET_KEY = os.getenv("SECRET_KEY", "smartreceipt-secret-key-change-in-production")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24  # 24 hours

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./smartreceipt.db")

UPLOAD_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "uploads")
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB
VECTORSTORE_DIR = os.getenv(
    "VECTORSTORE_DIR",
    os.path.join(os.path.dirname(os.path.dirname(__file__)), "vectorstore"),
)
RAG_EMBEDDING_MODEL = os.getenv("RAG_EMBEDDING_MODEL", "intfloat/multilingual-e5-small")

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-2.0-flash")

os.makedirs(UPLOAD_DIR, exist_ok=True)
os.makedirs(VECTORSTORE_DIR, exist_ok=True)
