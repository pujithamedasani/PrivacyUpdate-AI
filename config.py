import os
from pathlib import Path
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent

def reload_env():
    """Dynamically reload .env from disk so updates take effect immediately."""
    env_file = BASE_DIR / ".env"
    if env_file.exists():
        load_dotenv(env_file, override=True)

# Initial load
reload_env()

class Config:
    SECRET_KEY = os.getenv("SECRET_KEY", "privacyupdate-ai-secure-secret-key-2026")
    BASE_DIR = BASE_DIR
    DATABASE_PATH = Path(os.getenv("DATABASE_PATH", BASE_DIR / "data" / "privacyupdate.db"))
    UPLOAD_FOLDER = Path(os.getenv("UPLOAD_FOLDER", BASE_DIR / "uploads"))
    MAX_CONTENT_LENGTH = 32 * 1024 * 1024  # 32 MB max upload size
    ALLOWED_EXTENSIONS = {"pdf", "docx", "doc", "txt", "md", "zip", "json", "png", "jpg"}
    
    FIRECRAWL_API_URL = os.getenv("FIRECRAWL_API_URL", "https://api.firecrawl.dev/v1")
    MEMENTO_TIMEMAP_URL = os.getenv("MEMENTO_TIMEMAP_URL", "http://timetravel.mementoweb.org/timemap/json/")
    WAYBACK_TIMEMAP_URL = "https://web.archive.org/cdx/search/cdx"

    @classmethod
    def get_firecrawl_api_key(cls):
        reload_env()
        key = os.getenv("FIRECRAWL_API_KEY", "").strip()
        return key.strip("\"'")

    @classmethod
    def get_openai_api_key(cls):
        reload_env()
        key = os.getenv("OPENAI_API_KEY", "").strip()
        return key.strip("\"'")

    @classmethod
    def get_openai_model(cls):
        reload_env()
        return os.getenv("OPENAI_MODEL", "gpt-4o-mini").strip()

    # Legacy static getters for backward compatibility
    @property
    def FIRECRAWL_API_KEY(self):
        return self.get_firecrawl_api_key()

    @property
    def OPENAI_API_KEY(self):
        return self.get_openai_api_key()

    @property
    def OPENAI_MODEL(self):
        return self.get_openai_model()

    @classmethod
    def ensure_directories(cls):
        cls.DATABASE_PATH.parent.mkdir(parents=True, exist_ok=True)
        cls.UPLOAD_FOLDER.mkdir(parents=True, exist_ok=True)
