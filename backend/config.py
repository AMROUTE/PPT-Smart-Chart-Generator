from __future__ import annotations

import os
from dataclasses import dataclass
from functools import lru_cache

from dotenv import load_dotenv

load_dotenv()


@dataclass(frozen=True)
class Settings:
    app_name: str = "PPT Smart Chart Generator API"
    version: str = "2.0.0"
    host: str = os.getenv("HOST", "0.0.0.0")
    port: int = int(os.getenv("PORT", "8000"))
    upload_dir: str = os.getenv("UPLOAD_DIR", "data/uploads")
    output_dir: str = os.getenv("OUTPUT_DIR", "outputs")
    log_dir: str = os.getenv("LOG_DIR", "logs")
    max_retries: int = int(os.getenv("PIPELINE_MAX_RETRIES", "2"))
    enable_qwen_api: bool = os.getenv("ENABLE_QWEN_API", "1") == "1"
    qwen_api_key: str = os.getenv("QWEN_API_KEY", "")
    qwen_model: str = os.getenv("QWEN_MODEL", os.getenv("MODEL_NAME", "qwen-plus"))
    qwen_base_url: str = os.getenv(
        "QWEN_BASE_URL",
        "https://dashscope.aliyuncs.com/compatible-mode/v1/chat/completions",
    )
    qwen_timeout_seconds: int = int(os.getenv("QWEN_TIMEOUT_SECONDS", "25"))
    cors_origins: tuple[str, ...] = ("*",)


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()
