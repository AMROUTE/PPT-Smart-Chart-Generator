from __future__ import annotations

import logging
import shutil
from datetime import datetime
from functools import lru_cache
from pathlib import Path
from typing import Any

from backend.config import get_settings
from backend.schemas import AgentState, PipelineInput

try:
    from langgraph.graph import END, StateGraph
except ModuleNotFoundError:  # pragma: no cover
    END = "__END__"
    StateGraph = None


PIPELINE_NODES = ["parse_ppt", "semantic_analysis", "generate_chart", "generate_illustration", "save_pptx"]

STEP_PROGRESS = {"parse_ppt": 20, "semantic_analysis": 40, "generate_chart": 65, "generate_illustration": 85, "save_pptx": 100}

ILLUSTRATION_FORBIDDEN_TERMS = {"chart", "charts", "graph", "graphs", "dashboard", "bar", "line", "pie", "scatter", "heatmap"}


def _normalize_chart_override(chart_type: str | None) -> str:
    normalized = (chart_type or "").strip().lower()
    allowed = {"bar", "line", "pie", "scatter", "area", "histogram", "box", "heatmap"}
    return normalized if normalized in allowed else ""


def _normalize_illustration_style(style: str | None) -> str:
    normalized = (style or "auto").strip().lower()
    return normalized if normalized in {"auto", "business", "tech", "education", "medical", "academic", "sketch"} else "auto"


def _normalize_image_model(model: str | None) -> str:
    normalized = (model or "local").strip().lower()
    return normalized if normalized in {"local", "flux", "wanx"} else "local"


def _normalize_chart_theme(theme: str | None) -> str:
    normalized = (theme or "tech").strip().lower()
    return normalized if normalized in {"tech", "business", "minimal", "academic"} else "tech"


def _sanitize_illustration_text(text: str) -> str:
    sanitized = text or ""
    for term in ILLUSTRATION_FORBIDDEN_TERMS:
        sanitized = sanitized.replace(term, "")
        sanitized = sanitized.replace(term.title(), "")
        sanitized = sanitized.replace(term.upper(), "")
    return " ".join(part for part in sanitized.split() if part.strip()).strip(" ,.;")


def _sanitize_keywords(keywords: list[str]) -> list[str]:
    sanitized: list[str] = []
    for keyword in keywords:
        cleaned = _sanitize_illustration_text(str(keyword))
        if cleaned and cleaned not in sanitized:
            sanitized.append(cleaned)
    return sanitized


def _build_illustration_prompt(visual_theme: str, style_hint: str, image_model: str, summary: str, keywords: list[str], audience: str) -> str:
    sanitized_theme = _sanitize_illustration_text(visual_theme) or "business scenario illustration"
    sanitized_summary = _sanitize_illustration_text(summary)
    sanitized_keywords = _sanitize_keywords(keywords)
    style_text = "auto" if style_hint == "auto" else style_hint
    parts = [f"Theme: {sanitized_theme}", f"Style: {style_text}", f"Audience: {audience or 'business'}"]
    if sanitized_summary:
        parts.append(f"Direction: {sanitized_summary}")
    if sanitized_keywords:
        parts.append(f"Keywords: {', '.join(sanitized_keywords[:4])}")
    parts.append("Avoid charts, axes, dashboards, or explicit statistical graphics in the illustration.")
    parts.append(f"Model: {image_model}")
    return " | ".join(parts)


def _estimate_clip_score(text_content: str, visual_theme: str, keywords: list[str], style: str, image_model: str) -> float:
    base = 6.2
    text_lower = text_content.lower()
    if any(keyword.lower() in text_lower for keyword in keywords):
        base += 0.6
    if any(marker in text_lower for marker in ["growth", "trend", "revenue", "share", "education", "medical", "tech", "business"]):
        base += 0.4
    if style != "auto":
        base += 0.3
    if image_model in {"flux", "wanx"}:
        base += 0.2
    if visual_theme:
        base += 0.2
    return round(min(base, 9.4), 2)


@lru_cache(maxsize=1)
def _get_logger() -> logging.Logger:
    settings = get_settings()
    log_dir = Path(settings.log_dir)
    log_dir.mkdir(parents=True, exist_ok=True)
    logger = logging.getLogger("ppt_pipeline")
    if not logger.handlers:
        handler = logging.FileHandler(log_dir / "pipeline.log", encoding="utf-8")
        formatter = logging.Formatter("%(asctime)s [%(levelname)s] %(message)s")
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        logger.setLevel(logging.INFO)
    return logger


def append_log(state: dict[str, Any], message: str, level: str = "info") -> dict[str, Any]:
    state.setdefault("logs", [])
    timestamped = f"{datetime.now().strftime('%H:%M:%S')} {message}"
    state["logs"].append(timestamped)
    request_id = state.get("request_id", "unknown")
    logger = _get_logger()
    getattr(logger, level, logger.info)(f"[{request_id}] {message}")
    return state


def parse_ppt_node(state: dict[str, Any]) -> dict[str, Any]:
    from backend.ppt_parser import extract_slide_content

    ppt_path = Path(state["ppt_path"])
    if state.get("extracted_tables"):
        return append_log(state, "PPT parsing skipped because preloaded data already exists.")

    try:
        parsed = extract_slide_content(ppt_path, state["current_slide"])
        state["text_content"] = parsed.text_content or f"Parsed slide {state['current_slide']} from {ppt_path.name}"
        state["extracted_tables"] = [{"title": table["title"], "columns": table["columns"], "rows": table["rows"], "cell_matrix": table.get("cell_matrix", []), "merge_hints": table.get("merge_hints", []), "raw_matrix": table.get("raw_matrix", [])} for table in parsed.tables]
        state["shapes"] = parsed.shapes
        if not state["extracted_tables"]:
            raise ValueError("No table found in slide content.")
        return append_log(state, "PPT parsing completed from source file.")
    except Exception as exc:
        state["text_content"] = f"Parsed slide {state['current_slide']} from {ppt_path.name}"
        state["extracted_tables"] = [{"title": "sample_table", "columns": ["category", "value"], "rows": [["Q1", 120], ["Q2", 180], ["Q3", 156]], "cell_matrix": [], "merge_hints": [], "raw_matrix": []}]
        state["shapes"] = []
        append_log(state, f"PPT parser fallback enabled: {exc}", "warning")
        return append_log(state, "PPT parsing fallback completed.")


def semantic_analysis_node(state: dict[str, Any]) -> dict[str, Any]:
    semantic_mode = str(state.get("semantic_mode", "local")).strip().lower() or "local"
    chart_override = _normalize_chart_override(state.get("chart_type_override"))
    chart_theme = _normalize_chart_theme(state.get("chart_theme"))
    illustration_style = _normalize_illustration_style(state.get("illustration_style"))
    image_model = _normalize_image_model(state.get("image_model"))
    text_content = (state.get("text_content") or "").lower()
    table = (state.get("extracted_tables") or [{}])[0]
    columns = table.get("columns", [])
    rows = table.get("rows", [])
    table_summary = f"columns={columns}; sample_rows={rows[:4]}"

    def looks_like_time_label(value: Any) -> bool:
        text = str(value).lower()
        markers = ["q1", "q2", "q3", "q4", "202", "week", "wk", "jan", "feb", "mar"]
        return any(marker in text for marker in markers)

    numeric_column_indexes: list[int] = []
    for index, column in enumerate(columns):
        values = [row[index] for row in rows if len(row) > index]
        numeric_count = 0
        for value in values:
            try:
                float(value)
                numeric_count += 1
            except (TypeError, ValueError):
                continue
        if values and numeric_count >= max(1, len(values) // 2):
            numeric_column_indexes.append(index)

    first_column_values = [row[0] for row in rows if row]
    numeric_rows = len(rows)
    chart_type = "bar"
    if any(keyword in text_content for keyword in ["share", "portion", "composition"]):
        chart_type = "pie"
    elif any(keyword in text_content for keyword in ["trend", "growth", "change"]):
        chart_type = "line"
    elif first_column_values and all(looks_like_time_label(value) for value in first_column_values[: min(4, len(first_column_values))]):
        chart_type = "line"
    elif len(numeric_column_indexes) >= 2 and len(columns) <= 3:
        chart_type = "scatter"
    elif len(numeric_column_indexes) >= 3 and numeric_rows >= 4:
        chart_type = "heatmap"
    elif numeric_rows <= 6 and len(numeric_column_indexes) == 1:
        chart_type = "bar"
    elif numeric_rows > 8 and len(numeric_column_indexes) == 1:
        chart_type = "line"

    heuristic_result = {"task": "chart_generation", "chart_type": chart_override or chart_type, "chart_theme": chart_theme, "audience": "business", "summary": "Inferred from slide text, label pattern, and extracted table structure.", "reason": "Heuristic semantic inference based on text, labels, and table shape.", "visual_theme": "business office collaboration" if illustration_style == "auto" else f"{illustration_style} visual scene", "palette": ["deep-blue", "sky-blue"], "keywords": ["office space", "team collaboration", "business atmosphere"], "source": "heuristic", "semantic_mode": "local", "image_model": image_model, "illustration_style": illustration_style}

    if semantic_mode == "qwen":
        try:
            from backend.qwen_client import analyze_semantics_with_qwen
            llm_result = analyze_semantics_with_qwen(state.get("text_content", ""), table_summary, api_key=str(state.get("custom_qwen_api_key", "") or ""), model=str(state.get("custom_qwen_model", "") or ""))
            state["intent"] = {
                "task": "chart_generation",
                "chart_type": chart_override or llm_result["chart_type"],
                "chart_theme": chart_theme,
                "audience": llm_result["audience"],
                "summary": llm_result["title"],
                "reason": llm_result["reason"] if not chart_override else f"Chart type manually overridden to {chart_override} while keeping semantic result.",
                "visual_theme": llm_result["visual_theme"] if illustration_style == "auto" else f"{illustration_style} visual scene",
                "palette": llm_result["palette"],
                "keywords": _sanitize_keywords(llm_result["keywords"]),
                "source": "qwen",
                "model": get_settings().qwen_model,
                "semantic_mode": "qwen",
                "image_model": image_model,
                "illustration_style": illustration_style,
            }
            return append_log(state, "Semantic analysis completed with Qwen.")
        except Exception as exc:
            state["intent"] = {**heuristic_result, "reason": f"Qwen unavailable, fallback to heuristic: {exc}", "semantic_mode": "local"}
            append_log(state, f"Qwen semantic analysis unavailable, fallback to heuristic: {exc}", "warning")
            return append_log(state, "Semantic analysis completed with heuristic fallback.")

    if chart_override:
        heuristic_result["reason"] = f"Chart type manually overridden to {chart_override}."
    state["intent"] = heuristic_result
    return append_log(state, "Semantic analysis completed with local heuristic.")


def generate_chart_node(state: dict[str, Any]) -> dict[str, Any]:
    chart_type = state["intent"].get("chart_type", "bar")
    output_path = Path(get_settings().output_dir) / f"{state.get('request_id', 'req')}_chart_slide_{state['current_slide']}.png"
    tables = state.get("extracted_tables", [])
    try:
        from backend.chart_generator import generate_chart
        if not tables:
            raise ValueError("No extracted tables available for chart generation.")
        table = tables[0]
        columns = table.get("columns", [])
        rows = table.get("rows", [])
        if not columns or not rows:
            raise ValueError("Extracted table is empty.")
        records = [dict(zip(columns, row)) for row in rows]
        title = f"Slide {state['current_slide']} {chart_type.title()} Chart"
        chart = generate_chart(records, chart_type=chart_type, output_path=output_path, title=title, theme=str(state.get("chart_theme", "tech")))
        state["chart_spec"] = chart.to_dict()
        state["chart_image"] = chart.output_path
        return append_log(state, "Chart generation completed from extracted table.")
    except Exception as exc:
        fallback_path = _write_chart_fallback_png(output_path, state["current_slide"], tables, chart_type)
        state["chart_spec"] = {"chart_type": chart_type, "output_path": str(fallback_path), "title": f"Slide {state['current_slide']} chart recommendation", "theme": str(state.get("chart_theme", "tech")), "data_points": len(tables[0].get("rows", [])) if tables else 0, "fallback": True}
        state["chart_image"] = str(fallback_path)
        append_log(state, f"Chart generator fallback enabled: {exc}", "warning")
        return append_log(state, "Chart generation fallback completed.")


def _write_chart_fallback_png(output_path: Path, slide_number: int, tables: list[dict[str, Any]], chart_type: str) -> Path:
    from PIL import Image, ImageDraw, ImageFont
    png_path = output_path.with_suffix(".png")
    png_path.parent.mkdir(parents=True, exist_ok=True)
    rows = tables[0].get("rows", [])[:4] if tables else []
    image = Image.new("RGB", (1200, 700), "#132034")
    draw = ImageDraw.Draw(image)
    title_font = ImageFont.load_default()
    body_font = ImageFont.load_default()
    draw.rounded_rectangle((0, 0, 1199, 699), radius=28, outline="#132034", width=1)
    draw.text((120, 110), f"Slide {slide_number} {chart_type.title()} Preview", fill="#ffffff", font=title_font)
    draw.text((120, 155), "Fallback preview generated for local demo", fill="#9ac7ff", font=body_font)
    draw.line((100, 540, 1060, 540), fill="#4e6985", width=3)
    base_x = 130
    for index, row in enumerate(rows):
        label = str(row[0])
        try:
            value = float(row[1])
        except (ValueError, TypeError, IndexError):
            value = 0
        height = max(48, min(int(value * 1.35), 260))
        x = base_x + index * 180
        y = 540 - height
        draw.text((x + 10, 560), label, fill="#d7ebff", font=body_font)
        draw.rounded_rectangle((x, y, x + 84, 540), radius=16, fill="#5aa3ff")
    image.save(png_path)
    return png_path


def _write_illustration_png(output_path: Path, visual_theme: str, style_hint: str, image_model: str) -> None:
    from PIL import Image, ImageDraw, ImageFont
    output_path.parent.mkdir(parents=True, exist_ok=True)
    image = Image.new("RGB", (1200, 700), "#183250")
    draw = ImageDraw.Draw(image)
    title_font = ImageFont.load_default()
    body_font = ImageFont.load_default()
    draw.rounded_rectangle((0, 0, 1199, 699), radius=28, fill="#183250")
    draw.text((120, 110), "Illustration Preview", fill="#f7fbff", font=title_font)
    draw.text((120, 145), f"{style_hint.title()} style | {image_model.upper()}", fill="#d8ebff", font=body_font)
    draw.rounded_rectangle((120, 170, 430, 480), radius=44, outline="#2dd4bf", width=3)
    draw.ellipse((171, 221, 379, 429), outline="#2dd4bf", width=4)
    draw.line((205, 362, 260, 240, 322, 322, 380, 214), fill="#ecfeff", width=10)
    image.save(output_path)


def generate_illustration_node(state: dict[str, Any]) -> dict[str, Any]:
    style_hint = _normalize_illustration_style(state.get("illustration_style"))
    image_model = _normalize_image_model(state.get("image_model"))
    visual_theme = state["intent"].get("visual_theme", "intelligent illustration preview")
    state["illustration_prompt"] = _build_illustration_prompt(visual_theme=visual_theme, style_hint=style_hint, image_model=image_model, summary=str(state["intent"].get("summary", "")), keywords=list(state["intent"].get("keywords", [])), audience=str(state["intent"].get("audience", "business")))
    output_path = Path(get_settings().output_dir) / f"{state.get('request_id', 'req')}_illustration_slide_{state['current_slide']}.png"
    generation_source = "local"
    generation_warning = ""
    if image_model in {"wanx", "flux"}:
        try:
            from backend.image_clients import generate_flux_image, generate_wanx_image
            if image_model == "wanx":
                generate_wanx_image(state["illustration_prompt"], output_path, api_key=str(state.get("custom_wanx_api_key", "") or ""))
            else:
                generate_flux_image(state["illustration_prompt"], output_path, api_key=str(state.get("custom_flux_api_key", "") or ""))
            generation_source = image_model
            append_log(state, f"Illustration generated through {image_model.upper()} API.")
        except Exception as exc:
            generation_warning = str(exc)
            append_log(state, f"{image_model.upper()} illustration fallback enabled: {exc}", "warning")
    if generation_source == "local":
        _write_illustration_png(output_path, visual_theme=visual_theme, style_hint=style_hint, image_model=image_model)
    state["illustration_image"] = str(output_path)
    clip_score = _estimate_clip_score(state.get("text_content", ""), state["intent"].get("visual_theme", ""), _sanitize_keywords(state["intent"].get("keywords", [])), style_hint, image_model)
    state["illustration_meta"] = {"clip_score": clip_score, "score_source": "heuristic", "image_model": image_model, "illustration_style": style_hint, "generation_source": generation_source, "generation_warning": generation_warning, "regenerate_hint": clip_score < 6.5}
    state["intent"]["clip_score"] = clip_score
    state["intent"]["image_model"] = image_model
    state["intent"]["illustration_style"] = style_hint
    state["intent"]["keywords"] = _sanitize_keywords(state["intent"].get("keywords", []))
    return append_log(state, "Illustration preview asset generated.")


def save_pptx_node(state: dict[str, Any]) -> dict[str, Any]:
    from backend.insert_to_pptx import insert_generated_assets
    ppt_path = Path(state["ppt_path"])
    output_dir = Path(get_settings().output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    final_path = Path(state.get("output_ppt_path") or (output_dir / f"{ppt_path.stem}_enhanced{ppt_path.suffix}"))
    if ppt_path.exists():
        summary = state["intent"].get("reason") or "Auto-generated result"
        save_target = final_path
        if ppt_path.resolve() == final_path.resolve():
            save_target = final_path.with_name(f"{final_path.stem}_tmp{final_path.suffix}")
        try:
            insert_generated_assets(ppt_path=ppt_path, output_path=save_target, slide_number=state["current_slide"], chart_path=state.get("chart_image") or None, illustration_path=state.get("illustration_image") or None, title=f"Slide {state['current_slide']} enhanced result", subtitle=summary, intent=state.get("intent", {}), shapes=state.get("shapes", []))
            if save_target != final_path:
                shutil.move(str(save_target), str(final_path))
            state["final_pptx_path"] = str(final_path)
            return append_log(state, "Enhanced PPT saved with inserted chart assets.")
        except Exception as exc:
            if save_target != final_path and save_target.exists():
                save_target.unlink(missing_ok=True)
            if ppt_path.resolve() != final_path.resolve():
                shutil.copyfile(ppt_path, final_path)
            state["final_pptx_path"] = str(final_path)
            append_log(state, f"PPT writeback fallback enabled: {exc}", "warning")
            return append_log(state, "Enhanced PPT fallback copy saved.")
    final_path.write_bytes(b"")
    state["final_pptx_path"] = str(final_path)
    return append_log(state, "Enhanced PPT placeholder saved.")


class FallbackCompiledGraph:
    def __init__(self, nodes: list[tuple[str, Any]]):
        self._nodes = nodes
    def invoke(self, state: dict[str, Any]) -> dict[str, Any]:
        current = dict(state)
        for _, node in self._nodes:
            current = node(current)
        return current
    def get_graph(self) -> "FallbackCompiledGraph":
        return self
    def draw_mermaid(self) -> str:
        return "\n".join(["graph TD", "    start([Start]) --> parse_ppt", "    parse_ppt --> semantic_analysis", "    semantic_analysis --> generate_chart", "    generate_chart --> generate_illustration", "    generate_illustration --> save_pptx", "    save_pptx --> end([End])"])


def build_pipeline():
    node_pairs = [("parse_ppt", parse_ppt_node), ("semantic_analysis", semantic_analysis_node), ("generate_chart", generate_chart_node), ("generate_illustration", generate_illustration_node), ("save_pptx", save_pptx_node)]
    if StateGraph is None:
        return FallbackCompiledGraph(node_pairs)
    workflow = StateGraph(dict)
    for name, node in node_pairs:
        workflow.add_node(name, node)
    workflow.set_entry_point("parse_ppt")
    workflow.add_edge("parse_ppt", "semantic_analysis")
    workflow.add_edge("semantic_analysis", "generate_chart")
    workflow.add_edge("generate_chart", "generate_illustration")
    workflow.add_edge("generate_illustration", "save_pptx")
    workflow.add_edge("save_pptx", END)
    return workflow.compile()


@lru_cache(maxsize=1)
def get_pipeline_app():
    return build_pipeline()


def _record_stage(state: dict[str, Any], stage_name: str, status: str, details: str) -> None:
    state.setdefault("stage_history", [])
    state["stage_history"].append({"stage": stage_name, "status": status, "details": details, "progress": STEP_PROGRESS.get(stage_name, state.get("progress", 0)), "timestamp": datetime.now().isoformat(timespec="seconds")})


def _run_step_with_retry(state: dict[str, Any], step_name: str, step_fn: Any, max_retries: int) -> dict[str, Any]:
    attempts = 0
    while True:
        try:
            append_log(state, f"{step_name} started.")
            next_state = step_fn(state)
            next_state["progress"] = STEP_PROGRESS.get(step_name, next_state.get("progress", 0))
            _record_stage(next_state, step_name, "completed", f"{step_name} completed successfully.")
            return next_state
        except Exception as exc:
            attempts += 1
            state.setdefault("retry_counts", {})
            state["retry_counts"][step_name] = attempts
            append_log(state, f"{step_name} failed on attempt {attempts}: {exc}", "warning")
            if attempts > max_retries:
                state["status"] = "failed"
                _record_stage(state, step_name, "failed", str(exc))
                raise RuntimeError(f"Pipeline step '{step_name}' failed after {attempts} attempts.") from exc
            _record_stage(state, step_name, "retrying", f"Retry {attempts} scheduled after error: {exc}")


def run_pipeline(payload: PipelineInput | dict[str, Any]) -> dict[str, Any]:
    if isinstance(payload, PipelineInput):
        initial_state = AgentState(ppt_path=payload.ppt_path, request_id=payload.request_id, current_slide=payload.current_slide, semantic_mode=payload.semantic_mode, chart_type_override=payload.chart_type_override, chart_theme=payload.chart_theme, illustration_style=payload.illustration_style, image_model=payload.image_model, custom_qwen_api_key=payload.custom_qwen_api_key, custom_qwen_model=payload.custom_qwen_model, custom_wanx_api_key=payload.custom_wanx_api_key, custom_flux_api_key=payload.custom_flux_api_key).to_dict()
    else:
        initial_state = dict(payload)
        initial_state.setdefault("logs", [])
        initial_state.setdefault("stage_history", [])
        initial_state.setdefault("retry_counts", {})
        initial_state.setdefault("progress", 0)
        initial_state.setdefault("status", "pending")
        initial_state.setdefault("semantic_mode", "local")
        initial_state.setdefault("chart_type_override", "")
        initial_state.setdefault("chart_theme", "tech")
        initial_state.setdefault("illustration_style", "auto")
        initial_state.setdefault("image_model", "local")
    state = dict(initial_state)
    state["status"] = "running"
    append_log(state, "Pipeline execution started.")
    for step_name, step_fn in [("parse_ppt", parse_ppt_node), ("semantic_analysis", semantic_analysis_node), ("generate_chart", generate_chart_node), ("generate_illustration", generate_illustration_node), ("save_pptx", save_pptx_node)]:
        state = _run_step_with_retry(state, step_name, step_fn, get_settings().max_retries)
    state["status"] = "completed"
    append_log(state, "Pipeline execution completed.")
    return state


def export_pipeline_mermaid() -> str:
    return get_pipeline_app().get_graph().draw_mermaid()

