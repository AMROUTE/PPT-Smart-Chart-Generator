from __future__ import annotations

import os
from pathlib import Path
from tempfile import NamedTemporaryFile
from typing import Any, Dict, Optional

from main_pipeline import PipelineInput, export_pipeline_mermaid, run_pipeline

try:
    from fastapi import FastAPI, File, Form, HTTPException, UploadFile
    from fastapi.middleware.cors import CORSMiddleware
    from fastapi.responses import JSONResponse
except ModuleNotFoundError:  # pragma: no cover - local fallback for dependency-less environments
    FastAPI = None
    File = Form = UploadFile = HTTPException = JSONResponse = None
    CORSMiddleware = None


UPLOAD_DIR = Path("data/uploads")
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)


def allowed_file(filename: str) -> bool:
    return filename.lower().endswith(".pptx")


def build_file_metadata(file_path: Path, slide_number: int) -> Dict[str, Any]:
    return {
        "name": file_path.name,
        "size_bytes": file_path.stat().st_size if file_path.exists() else 0,
        "slide_number": slide_number,
        "suffix": file_path.suffix.lower(),
    }


def process_local_ppt(file_path: str | Path, slide_number: int) -> Dict[str, Any]:
    ppt_path = Path(file_path)
    if not ppt_path.exists():
        raise FileNotFoundError(f"PPT file not found: {ppt_path}")
    if not allowed_file(ppt_path.name):
        raise ValueError("Only .pptx files are supported.")

    metadata = build_file_metadata(ppt_path, slide_number)
    result = run_pipeline(
        PipelineInput(
            ppt_path=str(ppt_path),
            current_slide=slide_number,
        )
    )
    return {
        "message": "Pipeline completed successfully.",
        "file": metadata,
        "pipeline": result,
    }


def create_app() -> Optional["FastAPI"]:
    if FastAPI is None:
        return None

    app = FastAPI(
        title="PPT Smart Chart Generator API",
        version="1.0.0",
        description="Week 1 backend skeleton for the Vue-based PPT smart chart generator.",
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @app.get("/api/health")
    def health_check() -> Dict[str, Any]:
        return {
            "status": "ok",
            "frontend": "vue",
            "pipeline_engine": "langgraph" if "graph" in export_pipeline_mermaid() else "fallback",
        }

    @app.get("/api/pipeline")
    def get_pipeline_definition() -> Dict[str, str]:
        return {"mermaid": export_pipeline_mermaid()}

    @app.post("/api/process")
    async def process_upload(
        file: "UploadFile" = File(...),
        slide_number: int = Form(1),
    ) -> "JSONResponse":
        if not allowed_file(file.filename):
            raise HTTPException(status_code=400, detail="Please upload a .pptx file.")

        suffix = Path(file.filename).suffix
        with NamedTemporaryFile(delete=False, suffix=suffix, dir=UPLOAD_DIR) as temp_file:
            contents = await file.read()
            temp_file.write(contents)
            temp_path = Path(temp_file.name)

        try:
            payload = process_local_ppt(temp_path, slide_number)
            return JSONResponse(payload)
        except (FileNotFoundError, ValueError) as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc

    return app


app = create_app()


if __name__ == "__main__":
    if app is None:
        missing = ["fastapi", "uvicorn"]
        raise SystemExit(
            "FastAPI runtime dependencies are missing. "
            f"Install them first: pip install {' '.join(missing)}"
        )

    import uvicorn

    host = os.getenv("HOST", "0.0.0.0")
    port = int(os.getenv("PORT", "8000"))
    uvicorn.run(app, host=host, port=port)
