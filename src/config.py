"""集中配置：从环境变量 / .env 读取，绝不硬编码密钥。"""
import os
from dotenv import load_dotenv

load_dotenv()


class Settings:
    # --- LLM (DeepSeek，OpenAI 兼容接口) ---
    DEEPSEEK_API_KEY: str = os.getenv("DEEPSEEK_API_KEY", "")
    DEEPSEEK_BASE_URL: str = os.getenv("DEEPSEEK_BASE_URL", "https://api.deepseek.com")
    LLM_MODEL: str = os.getenv("LLM_MODEL", "deepseek-chat")

    # --- Spotify（可选：不配也能跑核心闭环）---
    SPOTIFY_CLIENT_ID: str = os.getenv("SPOTIFY_CLIENT_ID", "")
    SPOTIFY_CLIENT_SECRET: str = os.getenv("SPOTIFY_CLIENT_SECRET", "")
    REDIRECT_URI: str = os.getenv("REDIRECT_URI", "http://localhost:8888/callback")

    # --- 记忆 ---
    DB_PATH: str = os.getenv("DB_PATH", os.path.join(os.path.dirname(__file__), "..", "data", "memory.db"))

    # --- 可观测性 ---
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")

    @property
    def spotify_enabled(self) -> bool:
        return bool(self.SPOTIFY_CLIENT_ID and self.SPOTIFY_CLIENT_SECRET)

    @property
    def llm_ready(self) -> bool:
        return bool(self.DEEPSEEK_API_KEY)


settings = Settings()
