from __future__ import annotations

import os
from dataclasses import dataclass
from functools import lru_cache


@dataclass(frozen=True)
class Settings:
    app_name: str = "PPT Smart Chart Generator API"
    version: str = "1.0.0"
    host: str = os.getenv("HOST", "0.0.0.0")
    port: int = int(os.getenv("PORT", "8000"))
    upload_dir: str = os.getenv("UPLOAD_DIR", "data/uploads")
    cors_origins: tuple[str, ...] = ("*",)


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()
