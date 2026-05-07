from __future__ import annotations

from typing import Optional

from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles

from backend.config import get_settings
from backend.services import (
    allowed_file,
    build_slide_preview,
    build_health_payload,
    ensure_output_dir,
    ensure_upload_dir,
    process_local_ppt,
    process_demo_text,
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
    app.mount("/assets/outputs", StaticFiles(directory=ensure_output_dir()), name="outputs")
    app.mount("/assets/uploads", StaticFiles(directory=ensure_upload_dir()), name="uploads")

    @app.get("/api/health")
    def health_check() -> dict[str, str]:
        return build_health_payload()

    @app.get("/api/pipeline")
    def get_pipeline_definition() -> dict[str, str]:
        from backend.pipeline import export_pipeline_mermaid

        return {"mermaid": export_pipeline_mermaid()}

    @app.post("/api/process")
    async def process_upload(
        file: UploadFile = File(...),
        slide_number: int = Form(1),
        semantic_mode: str = Form("local"),
        chart_type_override: str = Form(""),
        illustration_style: str = Form("auto"),
        image_model: str = Form("local"),
    ) -> JSONResponse:
        if not file.filename or not allowed_file(file.filename):
            raise HTTPException(status_code=400, detail="Please upload a .pptx file.")

        temp_path = save_upload(file.filename, await file.read())
        try:
            payload = process_local_ppt(
                temp_path,
                slide_number,
                semantic_mode=semantic_mode,
                chart_type_override=chart_type_override,
                illustration_style=illustration_style,
                image_model=image_model,
            )
            return JSONResponse(payload)
        except (FileNotFoundError, ValueError) as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc
        except Exception as exc:
            raise HTTPException(status_code=500, detail=f"Pipeline processing failed: {exc}") from exc

    @app.post("/api/demo-chart")
    async def demo_chart(
        source_text: str = Form(...),
        semantic_mode: str = Form("local"),
        chart_type_override: str = Form(""),
        illustration_style: str = Form("auto"),
        image_model: str = Form("local"),
    ) -> JSONResponse:
        if not source_text.strip():
            raise HTTPException(status_code=400, detail="Please provide demo text.")
        try:
            payload = process_demo_text(
                source_text,
                semantic_mode=semantic_mode,
                chart_type_override=chart_type_override,
                illustration_style=illustration_style,
                image_model=image_model,
            )
            return JSONResponse(payload)
        except (FileNotFoundError, ValueError) as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc
        except Exception as exc:
            raise HTTPException(status_code=500, detail=f"Demo processing failed: {exc}") from exc

    @app.post("/api/slide-preview")
    async def slide_preview(
        file: Optional[UploadFile] = File(default=None),
        slide_number: int = Form(1),
        upload_token: str = Form(""),
    ) -> JSONResponse:
        if file is None and not upload_token.strip():
            raise HTTPException(status_code=400, detail="Please upload a .pptx file first.")
        if file is not None and file.filename and not allowed_file(file.filename):
            raise HTTPException(status_code=400, detail="Please upload a .pptx file.")

        temp_path = None
        if file is not None and file.filename:
            temp_path = save_upload(file.filename, await file.read())
        try:
            payload = build_slide_preview(slide_number, file_path=temp_path, upload_token=upload_token)
            return JSONResponse(payload)
        except (FileNotFoundError, ValueError) as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc
        except Exception as exc:
            raise HTTPException(status_code=500, detail=f"Slide preview failed: {exc}") from exc

    return app


app = create_app()
