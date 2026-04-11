from __future__ import annotations

from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from backend.config import get_settings
from backend.pipeline import export_pipeline_mermaid
from backend.services import (
    allowed_file,
    build_health_payload,
    process_local_ppt,
    save_upload,
)


def create_app() -> FastAPI:
    settings = get_settings()
    app = FastAPI(
        title=settings.app_name,
        version=settings.version,
        description="Integrated backend for the Vue-based PPT smart chart generator.",
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=list(settings.cors_origins),
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @app.get("/api/health")
    def health_check() -> dict[str, str]:
        return build_health_payload()

    @app.get("/api/pipeline")
    def get_pipeline_definition() -> dict[str, str]:
        return {"mermaid": export_pipeline_mermaid()}

    @app.post("/api/process")
    async def process_upload(
        file: UploadFile = File(...),
        slide_number: int = Form(1),
    ) -> JSONResponse:
        if not file.filename or not allowed_file(file.filename):
            raise HTTPException(status_code=400, detail="Please upload a .pptx file.")

        temp_path = save_upload(file.filename, await file.read())
        try:
            payload = process_local_ppt(temp_path, slide_number)
            return JSONResponse(payload)
        except (FileNotFoundError, ValueError) as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc

    return app


app = create_app()
