from __future__ import annotations

from pathlib import Path
from tempfile import NamedTemporaryFile
from typing import Any

from backend.config import get_settings
from backend.pipeline import export_pipeline_mermaid, run_pipeline
from backend.schemas import PipelineInput


def ensure_upload_dir() -> Path:
    upload_dir = Path(get_settings().upload_dir)
    upload_dir.mkdir(parents=True, exist_ok=True)
    return upload_dir


def allowed_file(filename: str) -> bool:
    return filename.lower().endswith(".pptx")


def build_file_metadata(file_path: Path, slide_number: int) -> dict[str, Any]:
    return {
        "name": file_path.name,
        "size_bytes": file_path.stat().st_size if file_path.exists() else 0,
        "slide_number": slide_number,
        "suffix": file_path.suffix.lower(),
    }


def process_local_ppt(file_path: str | Path, slide_number: int) -> dict[str, Any]:
    ppt_path = Path(file_path)
    if not ppt_path.exists():
        raise FileNotFoundError(f"PPT file not found: {ppt_path}")
    if not allowed_file(ppt_path.name):
        raise ValueError("Only .pptx files are supported.")

    metadata = build_file_metadata(ppt_path, slide_number)
    result = run_pipeline(PipelineInput(ppt_path=str(ppt_path), current_slide=slide_number))
    return {
        "message": "Pipeline completed successfully.",
        "file": metadata,
        "pipeline": result,
    }


def save_upload(filename: str, content: bytes) -> Path:
    suffix = Path(filename).suffix
    with NamedTemporaryFile(delete=False, suffix=suffix, dir=ensure_upload_dir()) as temp_file:
        temp_file.write(content)
        return Path(temp_file.name)


def build_health_payload() -> dict[str, Any]:
    mermaid = export_pipeline_mermaid()
    return {
        "status": "ok",
        "frontend": "vue",
        "pipeline_engine": "langgraph" if "graph" in mermaid else "fallback",
    }
