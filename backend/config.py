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
    database_path: str = os.getenv("DATABASE_PATH", "data/app.db")
    max_retries: int = int(os.getenv("PIPELINE_MAX_RETRIES", "2"))
    enable_qwen_api: bool = os.getenv("ENABLE_QWEN_API", "1") == "1"
    qwen_api_key: str = os.getenv("QWEN_API_KEY", "")
    qwen_model: str = os.getenv("QWEN_MODEL", os.getenv("MODEL_NAME", "qwen-plus"))
    qwen_base_url: str = os.getenv(
        "QWEN_BASE_URL",
        "https://dashscope.aliyuncs.com/compatible-mode/v1/chat/completions",
    )
    qwen_timeout_seconds: int = int(os.getenv("QWEN_TIMEOUT_SECONDS", "25"))
    wanx_api_key: str = os.getenv("WANX_API_KEY", os.getenv("QWEN_API_KEY", ""))
    wanx_model: str = os.getenv("WANX_MODEL", "wan2.6-t2i")
    wanx_base_url: str = os.getenv(
        "WANX_BASE_URL",
        "https://dashscope.aliyuncs.com/api/v1/services/aigc/multimodal-generation/generation",
    )
    flux_api_key: str = os.getenv("FLUX_API_KEY", "")
    flux_base_url: str = os.getenv("FLUX_BASE_URL", "https://api.bfl.ai/v1")
    flux_model_endpoint: str = os.getenv("FLUX_MODEL_ENDPOINT", "flux-pro-1.1")
    image_generation_timeout_seconds: int = int(os.getenv("IMAGE_GENERATION_TIMEOUT_SECONDS", "90"))
    image_poll_interval_seconds: float = float(os.getenv("IMAGE_POLL_INTERVAL_SECONDS", "1.5"))
    cors_origins: tuple[str, ...] = ("*",)


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()
