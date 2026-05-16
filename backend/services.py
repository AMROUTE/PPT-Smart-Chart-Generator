from __future__ import annotations

import re
import uuid
from pathlib import Path
from tempfile import NamedTemporaryFile
from typing import Any

from backend.config import get_settings
from backend.database import (
    database_health,
    fetch_upload_session,
    record_processing_job,
    record_slide_outline,
    record_upload_session,
)
from backend.schemas import PipelineInput


def ensure_upload_dir() -> Path:
    upload_dir = Path(get_settings().upload_dir)
    upload_dir.mkdir(parents=True, exist_ok=True)
    return upload_dir


def ensure_output_dir() -> Path:
    output_dir = Path(get_settings().output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    return output_dir


def ensure_preview_dir() -> Path:
    preview_dir = ensure_output_dir() / "previews"
    preview_dir.mkdir(parents=True, exist_ok=True)
    return preview_dir


def allowed_file(filename: str) -> bool:
    return filename.lower().endswith(".pptx")


def build_file_metadata(file_path: Path, slide_number: int) -> dict[str, Any]:
    return {
        "name": file_path.name,
        "size_bytes": file_path.stat().st_size if file_path.exists() else 0,
        "slide_number": slide_number,
        "suffix": file_path.suffix.lower(),
    }


def next_request_id(prefix: str = "req") -> str:
    return f"{prefix}-{uuid.uuid4().hex[:10]}"


def resolve_upload_token(upload_token: str) -> Path:
    token = Path(upload_token).name
    record = fetch_upload_session(token)
    target = Path(record["stored_path"]) if record else ensure_upload_dir() / token
    if not target.exists():
        raise FileNotFoundError("Uploaded PPT session not found. Please re-upload the file.")
    return target


def path_to_asset_url(file_path: str | Path) -> str:
    normalized = Path(file_path).as_posix().lstrip("./")
    if normalized.startswith("outputs/"):
        return f"/assets/{normalized}"
    if normalized.startswith("data/uploads/"):
        return f"/assets/{normalized}"
    return ""


def enrich_pipeline_assets(payload: dict[str, Any]) -> dict[str, Any]:
    chart_image = payload.get("chart_image")
    illustration_image = payload.get("illustration_image")
    final_pptx_path = payload.get("final_pptx_path")
    if chart_image:
        payload["chart_image_url"] = path_to_asset_url(chart_image)
    if illustration_image:
        payload["illustration_image_url"] = path_to_asset_url(illustration_image)
    if final_pptx_path:
        payload["final_pptx_url"] = path_to_asset_url(final_pptx_path)
    return payload


def normalize_semantic_mode(mode: str | None) -> str:
    normalized = (mode or "local").strip().lower()
    return normalized if normalized in {"local", "qwen"} else "local"


def normalize_chart_type_override(chart_type: str | None) -> str:
    normalized = (chart_type or "").strip().lower()
    allowed = {"", "auto", "bar", "line", "pie", "scatter", "area", "histogram", "box", "heatmap"}
    if normalized not in allowed:
        return ""
    return "" if normalized == "auto" else normalized


def normalize_illustration_style(style: str | None) -> str:
    normalized = (style or "auto").strip().lower()
    allowed = {"auto", "business", "tech", "education", "medical", "academic", "sketch"}
    return normalized if normalized in allowed else "auto"


def normalize_image_model(image_model: str | None) -> str:
    normalized = (image_model or "local").strip().lower()
    allowed = {"local", "flux", "wanx"}
    return normalized if normalized in allowed else "local"


def _normalize_slide_numbers(slide_numbers: list[int] | None, slide_count: int) -> list[int]:
    requested = slide_numbers or list(range(1, slide_count + 1))
    deduped: list[int] = []
    seen: set[int] = set()
    for slide_number in requested:
        value = int(slide_number)
        if value < 1 or value > slide_count:
            raise ValueError(f"Slide number {value} is out of range. This PPT has {slide_count} slides.")
        if value not in seen:
            deduped.append(value)
            seen.add(value)
    if not deduped:
        raise ValueError("At least one slide number is required for batch processing.")
    return deduped


def _record_job(result: dict[str, Any], upload_token: str, source_type: str, slide_number: int, semantic_mode: str, chart_type_override: str, illustration_style: str, image_model: str) -> None:
    record_processing_job(
        request_id=result["request_id"],
        upload_token=upload_token,
        source_type=source_type,
        slide_number=slide_number,
        semantic_mode=semantic_mode,
        chart_type_override=chart_type_override,
        illustration_style=illustration_style,
        image_model=image_model,
        status=result.get("status", "completed"),
        final_pptx_path=result.get("final_pptx_path", ""),
    )


def process_local_ppt(
    file_path: str | Path,
    slide_number: int,
    semantic_mode: str = "local",
    chart_type_override: str = "",
    illustration_style: str = "auto",
    image_model: str = "local",
    custom_qwen_api_key: str = "",
    custom_qwen_model: str = "",
    custom_wanx_api_key: str = "",
    custom_flux_api_key: str = "",
) -> dict[str, Any]:
    from backend.pipeline import run_pipeline

    ppt_path = Path(file_path)
    if not ppt_path.exists():
        raise FileNotFoundError(f"PPT file not found: {ppt_path}")
    if not allowed_file(ppt_path.name):
        raise ValueError("Only .pptx files are supported.")

    metadata = build_file_metadata(ppt_path, slide_number)
    resolved_mode = normalize_semantic_mode(semantic_mode)
    resolved_chart_type = normalize_chart_type_override(chart_type_override)
    resolved_style = normalize_illustration_style(illustration_style)
    resolved_model = normalize_image_model(image_model)
    result = run_pipeline(
        PipelineInput(
            ppt_path=str(ppt_path),
            current_slide=slide_number,
            request_id=next_request_id("ppt"),
            semantic_mode=resolved_mode,
            chart_type_override=resolved_chart_type,
            illustration_style=resolved_style,
            image_model=resolved_model,
            custom_qwen_api_key=custom_qwen_api_key.strip(),
            custom_qwen_model=custom_qwen_model.strip(),
            custom_wanx_api_key=custom_wanx_api_key.strip(),
            custom_flux_api_key=custom_flux_api_key.strip(),
        )
    )
    _record_job(result, ppt_path.name, "ppt", slide_number, resolved_mode, resolved_chart_type, resolved_style, resolved_model)
    enrich_pipeline_assets(result)
    return {
        "message": "Pipeline completed successfully.",
        "file": metadata,
        "semantic_mode": resolved_mode,
        "chart_type_override": resolved_chart_type,
        "illustration_style": resolved_style,
        "image_model": resolved_model,
        "pipeline": result,
    }


def process_local_ppt_batch(
    file_path: str | Path,
    slide_numbers: list[int] | None = None,
    semantic_mode: str = "local",
    chart_type_override: str = "",
    illustration_style: str = "auto",
    image_model: str = "local",
    custom_qwen_api_key: str = "",
    custom_qwen_model: str = "",
    custom_wanx_api_key: str = "",
    custom_flux_api_key: str = "",
) -> dict[str, Any]:
    from backend.pipeline import run_pipeline
    from backend.ppt_parser import extract_multiple_slide_contents, get_slide_count

    ppt_path = Path(file_path)
    if not ppt_path.exists():
        raise FileNotFoundError(f"PPT file not found: {ppt_path}")
    if not allowed_file(ppt_path.name):
        raise ValueError("Only .pptx files are supported.")

    slide_count = get_slide_count(ppt_path)
    target_slides = _normalize_slide_numbers(slide_numbers, slide_count)
    resolved_mode = normalize_semantic_mode(semantic_mode)
    resolved_chart_type = normalize_chart_type_override(chart_type_override)
    resolved_style = normalize_illustration_style(illustration_style)
    resolved_model = normalize_image_model(image_model)
    preloaded = extract_multiple_slide_contents(ppt_path, target_slides)
    batch_output_path = ensure_output_dir() / f"{ppt_path.stem}_batch_enhanced{ppt_path.suffix}"

    current_source = ppt_path
    slide_results: list[dict[str, Any]] = []
    for slide_number in target_slides:
        parsed = preloaded[slide_number]
        result = run_pipeline(
            {
                "request_id": next_request_id("batch"),
                "ppt_path": str(current_source),
                "current_slide": slide_number,
                "semantic_mode": resolved_mode,
                "chart_type_override": resolved_chart_type,
                "illustration_style": resolved_style,
                "image_model": resolved_model,
                "custom_qwen_api_key": custom_qwen_api_key.strip(),
                "custom_qwen_model": custom_qwen_model.strip(),
                "custom_wanx_api_key": custom_wanx_api_key.strip(),
                "custom_flux_api_key": custom_flux_api_key.strip(),
                "text_content": parsed.text_content,
                "extracted_tables": [
                    {
                        "title": table["title"],
                        "columns": table["columns"],
                        "rows": table["rows"],
                        "cell_matrix": table.get("cell_matrix", []),
                        "merge_hints": table.get("merge_hints", []),
                        "raw_matrix": table.get("raw_matrix", []),
                    }
                    for table in parsed.tables
                ],
                "shapes": parsed.shapes,
                "output_ppt_path": str(batch_output_path),
                "logs": [],
                "status": "pending",
                "progress": 0,
                "retry_counts": {},
                "stage_history": [],
            }
        )
        _record_job(result, ppt_path.name, "ppt-batch", slide_number, resolved_mode, resolved_chart_type, resolved_style, resolved_model)
        enrich_pipeline_assets(result)
        slide_results.append(result)
        current_source = Path(result["final_pptx_path"])

    return {
        "message": "Batch pipeline completed successfully.",
        "file": build_file_metadata(ppt_path, target_slides[0]),
        "slide_numbers": target_slides,
        "slide_count": slide_count,
        "processed_count": len(slide_results),
        "semantic_mode": resolved_mode,
        "chart_type_override": resolved_chart_type,
        "illustration_style": resolved_style,
        "image_model": resolved_model,
        "final_pptx_path": str(batch_output_path),
        "final_pptx_url": path_to_asset_url(batch_output_path),
        "slides": slide_results,
    }


def extract_records_from_text(source_text: str) -> list[dict[str, Any]]:
    matches = re.findall(
        r"([A-Za-z\u4e00-\u9fff][A-Za-z0-9\u4e00-\u9fff\s]{0,24})[:\s]*(\d+(?:\.\d+)?)",
        source_text,
    )
    records = [{"category": label.strip(), "value": float(value)} for label, value in matches]
    if records:
        return records

    trend_matches = re.findall(
        r"((?:20\d{2}|Q[1-4]|[A-Za-z]{3}|\d{1,2})\s*[,-]?\s*(\d+(?:\.\d+)?))",
        source_text,
    )
    if trend_matches:
        return [{"category": label.strip(), "value": float(value)} for label, value in trend_matches]

    return [
        {"category": "Q1", "value": 120},
        {"category": "Q2", "value": 165},
        {"category": "Q3", "value": 188},
        {"category": "Q4", "value": 210},
    ]


def process_demo_text(
    source_text: str,
    semantic_mode: str = "local",
    chart_type_override: str = "",
    illustration_style: str = "auto",
    image_model: str = "local",
    custom_qwen_api_key: str = "",
    custom_qwen_model: str = "",
    custom_wanx_api_key: str = "",
    custom_flux_api_key: str = "",
) -> dict[str, Any]:
    from backend.pipeline import run_pipeline

    records = extract_records_from_text(source_text)
    resolved_mode = normalize_semantic_mode(semantic_mode)
    resolved_chart_type = normalize_chart_type_override(chart_type_override)
    resolved_style = normalize_illustration_style(illustration_style)
    resolved_model = normalize_image_model(image_model)
    request_id = next_request_id("demo")
    result = run_pipeline(
        {
            "request_id": request_id,
            "ppt_path": "demo_text_input.pptx",
            "current_slide": 1,
            "semantic_mode": resolved_mode,
            "chart_type_override": resolved_chart_type,
            "illustration_style": resolved_style,
            "image_model": resolved_model,
            "custom_qwen_api_key": custom_qwen_api_key.strip(),
            "custom_qwen_model": custom_qwen_model.strip(),
            "custom_wanx_api_key": custom_wanx_api_key.strip(),
            "custom_flux_api_key": custom_flux_api_key.strip(),
            "text_content": source_text.strip(),
            "extracted_tables": [
                {
                    "title": "demo_metrics",
                    "columns": ["category", "value"],
                    "rows": [[record["category"], record["value"]] for record in records],
                }
            ],
            "logs": [],
            "status": "pending",
            "progress": 0,
            "retry_counts": {},
            "stage_history": [],
        }
    )
    _record_job(result, "demo", "demo", 1, resolved_mode, resolved_chart_type, resolved_style, resolved_model)
    enrich_pipeline_assets(result)
    return {
        "message": "Text-to-chart demo completed successfully.",
        "semantic_mode": resolved_mode,
        "chart_type_override": resolved_chart_type,
        "illustration_style": resolved_style,
        "image_model": resolved_model,
        "demo": {
            "source_text": source_text,
            "record_count": len(records),
        },
        "pipeline": result,
    }


def build_slide_preview(
    slide_number: int,
    file_path: str | Path | None = None,
    upload_token: str = "",
) -> dict[str, Any]:
    from backend.ppt_parser import get_slide_count, render_slide_preview

    if file_path is not None:
        ppt_path = Path(file_path)
    elif upload_token:
        ppt_path = resolve_upload_token(upload_token)
    else:
        raise ValueError("Please upload a .pptx file first.")

    if not ppt_path.exists():
        raise FileNotFoundError(f"PPT file not found: {ppt_path}")
    if not allowed_file(ppt_path.name):
        raise ValueError("Only .pptx files are supported.")

    preview_path = ensure_preview_dir() / f"{ppt_path.stem}_slide_{slide_number}_preview.png"
    preview = render_slide_preview(ppt_path, slide_number, preview_path)
    return {
        "message": "Slide preview generated successfully.",
        "upload_token": ppt_path.name,
        "slide_number": preview.slide_number,
        "slide_count": preview.slide_count or get_slide_count(ppt_path),
        "preview_image": preview.output_path,
        "preview_image_url": path_to_asset_url(preview.output_path),
        "file": build_file_metadata(ppt_path, slide_number),
    }


def parse_presentation_slides(file_path: str | Path | None = None, upload_token: str = "") -> dict[str, Any]:
    from backend.ppt_parser import get_slide_count, parse_presentation_outline

    if file_path is not None:
        ppt_path = Path(file_path)
    elif upload_token:
        ppt_path = resolve_upload_token(upload_token)
    else:
        raise ValueError("Please upload a .pptx file first.")

    if not ppt_path.exists():
        raise FileNotFoundError(f"PPT file not found: {ppt_path}")
    if not allowed_file(ppt_path.name):
        raise ValueError("Only .pptx files are supported.")

    slides = parse_presentation_outline(ppt_path)
    slides_payload = [item.to_dict() for item in slides]
    record_slide_outline(ppt_path.name, slides_payload)
    return {
        "message": "Presentation outline parsed successfully.",
        "upload_token": ppt_path.name,
        "slide_count": get_slide_count(ppt_path),
        "slides": slides_payload,
        "file": build_file_metadata(ppt_path, 1),
    }


def save_upload(filename: str, content: bytes) -> Path:
    suffix = Path(filename).suffix
    with NamedTemporaryFile(delete=False, suffix=suffix, dir=ensure_upload_dir()) as temp_file:
        temp_file.write(content)
        saved_path = Path(temp_file.name)
    record_upload_session(saved_path.name, filename, saved_path, saved_path.stat().st_size)
    return saved_path


def build_health_payload() -> dict[str, Any]:
    from backend.pipeline import export_pipeline_mermaid

    settings = get_settings()
    mermaid = export_pipeline_mermaid()
    database_payload = database_health()
    return {
        "status": "ok",
        "frontend": "vue",
        "pipeline_engine": "langgraph" if "graph" in mermaid else "fallback",
        "qwen_enabled": bool(settings.enable_qwen_api and settings.qwen_api_key),
        "qwen_model": settings.qwen_model,
        "wanx_enabled": bool(settings.wanx_api_key),
        "wanx_model": settings.wanx_model,
        "flux_enabled": bool(settings.flux_api_key),
        "flux_model_endpoint": settings.flux_model_endpoint,
        "semantic_modes": ["local", "qwen"],
        "image_models": ["local", "flux", "wanx"],
        "illustration_styles": ["auto", "business", "tech", "education", "medical", "academic", "sketch"],
        "features": [
            "retry-logging",
            "chart-preview",
            "illustration-preview",
            "demo-chart",
            "ppt-writeback",
            "chart-override",
            "style-selection",
            "sqlite-database",
            "tech-chart-theme",
            "batch-processing",
        ],
        **database_payload,
    }
