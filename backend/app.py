from __future__ import annotations

from typing import Any, Optional

from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles

from backend.config import get_settings
from backend.database import authenticate_or_create_user, fetch_processing_job, init_db, list_recent_jobs
from backend.services import (
    allowed_file,
    build_health_payload,
    build_slide_preview,
    ensure_output_dir,
    ensure_upload_dir,
    parse_presentation_slides,
    process_ppt_batch,
    process_demo_text,
    process_local_ppt,
    process_local_ppt_batch,
    path_to_asset_url,
    save_upload,
)


def create_app() -> FastAPI:
    settings = get_settings()
    init_db()
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
    def health_check() -> dict[str, Any]:
        return build_health_payload()

    @app.get("/api/pipeline")
    def get_pipeline_definition() -> dict[str, str]:
        from backend.pipeline import export_pipeline_mermaid

        return {"mermaid": export_pipeline_mermaid()}

    @app.post("/api/auth/login")
    async def login(username: str = Form(...), password: str = Form(...)) -> JSONResponse:
        try:
            user = authenticate_or_create_user(username, password)
            return JSONResponse(
                {
                    "message": "Login successful.",
                    "user": user,
                }
            )
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc

    @app.post("/api/process")
    async def process_upload(
        file: UploadFile = File(...),
        slide_number: int = Form(1),
        semantic_mode: str = Form("local"),
        chart_type_override: str = Form(""),
        chart_theme: str = Form("tech"),
        illustration_style: str = Form("auto"),
        image_model: str = Form("local"),
        custom_qwen_api_key: str = Form(""),
        custom_qwen_model: str = Form(""),
        custom_wanx_api_key: str = Form(""),
        custom_flux_api_key: str = Form(""),
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
                chart_theme=chart_theme,
                illustration_style=illustration_style,
                image_model=image_model,
                custom_qwen_api_key=custom_qwen_api_key,
                custom_qwen_model=custom_qwen_model,
                custom_wanx_api_key=custom_wanx_api_key,
                custom_flux_api_key=custom_flux_api_key,
            )
            return JSONResponse(payload)
        except (FileNotFoundError, ValueError) as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc
        except Exception as exc:
            raise HTTPException(status_code=500, detail=f"Pipeline processing failed: {exc}") from exc

    @app.post("/api/process-batch")
    async def process_upload_batch(
        file: Optional[UploadFile] = File(default=None),
        slide_numbers: str = Form(""),
        upload_token: str = Form(""),
        slide_start: int = Form(1),
        slide_end: int = Form(0),
        semantic_mode: str = Form("local"),
        chart_type_override: str = Form(""),
        chart_theme: str = Form("tech"),
        illustration_style: str = Form("auto"),
        image_model: str = Form("local"),
        custom_qwen_api_key: str = Form(""),
        custom_qwen_model: str = Form(""),
        custom_wanx_api_key: str = Form(""),
        custom_flux_api_key: str = Form(""),
    ) -> JSONResponse:
        if file is None and not upload_token.strip():
            raise HTTPException(status_code=400, detail="Please upload a .pptx file first.")
        if file is not None and file.filename and not allowed_file(file.filename):
            raise HTTPException(status_code=400, detail="Please upload a .pptx file.")

        temp_path = None
        if file is not None and file.filename:
            temp_path = save_upload(file.filename, await file.read())
        else:
            from backend.services import resolve_upload_token

            temp_path = resolve_upload_token(upload_token)
        try:
            parsed_slide_numbers = [int(item.strip()) for item in slide_numbers.split(",") if item.strip()] if slide_numbers.strip() else None
            if parsed_slide_numbers:
                payload = process_local_ppt_batch(
                    temp_path,
                    parsed_slide_numbers,
                    semantic_mode=semantic_mode,
                    chart_type_override=chart_type_override,
                    chart_theme=chart_theme,
                    illustration_style=illustration_style,
                    image_model=image_model,
                    custom_qwen_api_key=custom_qwen_api_key,
                    custom_qwen_model=custom_qwen_model,
                    custom_wanx_api_key=custom_wanx_api_key,
                    custom_flux_api_key=custom_flux_api_key,
                )
            else:
                payload = process_ppt_batch(
                    temp_path,
                    slide_start=slide_start,
                    slide_end=slide_end or None,
                    semantic_mode=semantic_mode,
                    chart_type_override=chart_type_override,
                    chart_theme=chart_theme,
                    illustration_style=illustration_style,
                    image_model=image_model,
                    custom_qwen_api_key=custom_qwen_api_key,
                    custom_qwen_model=custom_qwen_model,
                    custom_wanx_api_key=custom_wanx_api_key,
                    custom_flux_api_key=custom_flux_api_key,
                )
            return JSONResponse(payload)
        except (FileNotFoundError, ValueError) as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc
        except Exception as exc:
            raise HTTPException(status_code=500, detail=f"Batch processing failed: {exc}") from exc

    @app.post("/api/demo-chart")
    async def demo_chart(
        source_text: str = Form(...),
        semantic_mode: str = Form("local"),
        chart_type_override: str = Form(""),
        chart_theme: str = Form("tech"),
        illustration_style: str = Form("auto"),
        image_model: str = Form("local"),
        custom_qwen_api_key: str = Form(""),
        custom_qwen_model: str = Form(""),
        custom_wanx_api_key: str = Form(""),
        custom_flux_api_key: str = Form(""),
    ) -> JSONResponse:
        if not source_text.strip():
            raise HTTPException(status_code=400, detail="Please provide demo text.")
        try:
            payload = process_demo_text(
                source_text,
                semantic_mode=semantic_mode,
                chart_type_override=chart_type_override,
                chart_theme=chart_theme,
                illustration_style=illustration_style,
                image_model=image_model,
                custom_qwen_api_key=custom_qwen_api_key,
                custom_qwen_model=custom_qwen_model,
                custom_wanx_api_key=custom_wanx_api_key,
                custom_flux_api_key=custom_flux_api_key,
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

    @app.post("/api/parse-slides")
    async def parse_slides(
        file: Optional[UploadFile] = File(default=None),
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
            payload = parse_presentation_slides(file_path=temp_path, upload_token=upload_token)
            return JSONResponse(payload)
        except (FileNotFoundError, ValueError) as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc
        except Exception as exc:
            raise HTTPException(status_code=500, detail=f"Slide parsing failed: {exc}") from exc

    @app.get("/api/jobs")
    def jobs(limit: int = 30) -> JSONResponse:
        return JSONResponse({"jobs": list_recent_jobs(limit=limit)})

    @app.get("/api/jobs/{request_id}")
    def job_detail(request_id: str) -> JSONResponse:
        job = fetch_processing_job(request_id)
        if job is None:
            raise HTTPException(status_code=404, detail="Processing job not found.")
        job["chart_image_url"] = path_to_asset_url(job.get("chart_image_path", ""))
        job["illustration_image_url"] = path_to_asset_url(job.get("illustration_image_path", ""))
        job["final_pptx_url"] = path_to_asset_url(job.get("final_pptx_path", ""))
        return JSONResponse({"job": job})

    return app


app = create_app()
