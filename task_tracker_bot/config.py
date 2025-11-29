"""
Конфигурация приложения
"""
import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    BOT_TOKEN = os.getenv("BOT_TOKEN")
    DATABASE_PATH = os.getenv("DATABASE_PATH", "data/tasks.db")
    TASKS_PER_PAGE = int(os.getenv("TASKS_PER_PAGE", "10"))
    TIMEZONE = os.getenv("TIMEZONE", "Europe/Moscow")
    
    # io.net AI API настройки
    IO_NET_API_KEY = os.getenv("IO_NET_API_KEY")
    IO_NET_MODEL = os.getenv("IO_NET_MODEL", "deepseek-ai/DeepSeek-R1-0528")
    IO_NET_TEMPERATURE = float(os.getenv("IO_NET_TEMPERATURE", "0.3"))
    IO_NET_MAX_TOKENS = int(os.getenv("IO_NET_MAX_TOKENS", "2000"))
    IO_NET_API_URL = os.getenv("IO_NET_API_URL", "https://api.intelligence.io.solutions/api/v1/chat/completions")
    IO_NET_TIMEOUT = int(os.getenv("IO_NET_TIMEOUT", "60"))
    IO_NET_RETRY_COUNT = int(os.getenv("IO_NET_RETRY_COUNT", "3"))
    IO_NET_RETRY_DELAY = float(os.getenv("IO_NET_RETRY_DELAY", "1.0"))
    ORCHESTRATOR_CACHE_TTL = int(os.getenv("ORCHESTRATOR_CACHE_TTL", "300"))

