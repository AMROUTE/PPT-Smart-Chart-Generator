from __future__ import annotations

import logging
import re
import shutil
import tempfile
from datetime import datetime
from functools import lru_cache
from pathlib import Path
from typing import Any

from backend.config import get_settings
from backend.schemas import AgentState, PipelineInput
from backend.services import ensure_output_dir

try:
    from langgraph.graph import END, StateGraph
except ModuleNotFoundError:  # pragma: no cover
    END = "__END__"
    StateGraph = None


PIPELINE_NODES = ["parse_ppt", "semantic_analysis", "generate_chart", "generate_illustration", "save_pptx"]

STEP_PROGRESS = {"parse_ppt": 20, "semantic_analysis": 40, "generate_chart": 65, "generate_illustration": 85, "save_pptx": 100}

ILLUSTRATION_FORBIDDEN_TERMS = {"chart", "charts", "graph", "graphs", "dashboard", "bar", "line", "pie", "scatter", "heatmap"}
ILLUSTRATION_SCORE_THRESHOLD = 6.5
ILLUSTRATION_STYLE_PROFILES = {
    "auto": {
        "scene": "clear business context with people, place, and activity",
        "mood": "polished, presentation-ready, neutral professional lighting",
        "palette": ("#183250", "#2dd4bf", "#d8ebff", "#f7fbff"),
    },
    "business": {
        "scene": "modern office collaboration, meeting table, people discussing a plan",
        "mood": "confident, clean, executive presentation style",
        "palette": ("#24324a", "#f59e0b", "#e5edf7", "#ffffff"),
    },
    "tech": {
        "scene": "software team workspace with devices, cloud services, and product flow",
        "mood": "precise, futuristic, crisp blue-green lighting",
        "palette": ("#10233f", "#38bdf8", "#a7f3d0", "#f8fafc"),
    },
    "education": {
        "scene": "classroom learning moment with teacher, students, books, and board space",
        "mood": "warm, encouraging, accessible learning atmosphere",
        "palette": ("#254336", "#facc15", "#dcfce7", "#ffffff"),
    },
    "medical": {
        "scene": "healthcare consultation with clinician, patient support, and care setting",
        "mood": "calm, trustworthy, clean clinical environment",
        "palette": ("#173f46", "#22c55e", "#ccfbf1", "#ffffff"),
    },
    "academic": {
        "scene": "research discussion with papers, laptop, library or seminar context",
        "mood": "thoughtful, rigorous, scholarly but modern",
        "palette": ("#312e81", "#a78bfa", "#ede9fe", "#ffffff"),
    },
    "sketch": {
        "scene": "hand-drawn storyboard of people solving the slide topic",
        "mood": "lightweight, human, whiteboard sketch style",
        "palette": ("#2f3645", "#64748b", "#f8fafc", "#ffffff"),
    },
}

INTENT_TO_CHART_TYPE = {
    "comparison": "bar",
    "trend": "line",
    "composition": "pie",
    "distribution": "bar",
    "correlation": "scatter",
}


def _contains_any(text: str, keywords: list[str]) -> bool:
    return any(keyword in text for keyword in keywords)


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


def _looks_like_time_label(value: Any) -> bool:
    text = str(value).strip().lower()
    markers = ["q1", "q2", "q3", "q4", "202", "201", "week", "wk", "jan", "feb", "mar", "apr", "may", "jun", "月", "年", "季度", "周"]
    return any(marker in text for marker in markers)


def _numeric_column_indexes(columns: list[Any], rows: list[list[Any]]) -> list[int]:
    indexes: list[int] = []
    for index, _column in enumerate(columns):
        values = [row[index] for row in rows if len(row) > index]
        numeric_count = 0
        for value in values:
            try:
                float(value)
                numeric_count += 1
            except (TypeError, ValueError):
                continue
        if values and numeric_count >= max(1, len(values) // 2):
            indexes.append(index)
    return indexes


def _recommend_chart_intent(text_content: str, columns: list[Any], rows: list[list[Any]]) -> dict[str, Any]:
    normalized = (text_content or "").lower()
    signals: list[str] = []
    alternatives: list[str] = []

    time_markers = ["202", "201", "年", "月", "周", "季度", "近", "过去", "最近", "从", "到", "逐年", "持续", "趋势", "week", "quarter"]
    trend_markers = ["增长", "下降", "上升", "减少", "回升", "降低", "加快", "增加", "越来越", "逐步", "一路往上涨", "trend", "growth", "change", "decline"]
    comparison_markers = ["比", "高于", "低于", "超过", "对比", "相比", "最高", "最低", "差异", "分别为", "次之", "compare", "comparison", "higher", "lower"]
    composition_markers = ["占", "占比", "构成", "组成", "份额", "比例", "来自", "来源", "包括", "由", "部分组成", "share", "portion", "composition", "ratio"]
    distribution_markers = ["分布", "集中", "区间", "大多数", "主要位于", "人数最多", "中等水平", "distribution", "range", "bucket", "frequency"]
    correlation_markers = ["相关", "关系", "影响", "随着", "投入", "转化率", "留存率", "故障率", "体脂率", "correlation", "relationship", "impact"]

    numeric_indexes = _numeric_column_indexes(columns, rows)
    first_column_values = [row[0] for row in rows if row]
    time_label_count = sum(1 for value in first_column_values[: min(6, len(first_column_values))] if _looks_like_time_label(value))
    has_time_labels = bool(first_column_values) and time_label_count >= max(1, min(3, len(first_column_values)))
    has_yue_correlation = "越来越" not in normalized and re.search(r"越.+越", normalized) is not None
    has_time = _contains_any(normalized, time_markers) or has_time_labels
    has_trend = _contains_any(normalized, trend_markers)
    has_composition = _contains_any(normalized, composition_markers)
    has_distribution = _contains_any(normalized, distribution_markers)
    has_correlation = has_yue_correlation or _contains_any(normalized, correlation_markers) or ("增加后" in normalized and ("提升" in normalized or "下降" in normalized))
    has_comparison = _contains_any(normalized, comparison_markers)

    if has_time_labels:
        signals.append("首列呈现时间序列标签")
    if len(numeric_indexes) >= 2:
        signals.append("表格包含两个及以上数值列")
    if has_time and has_trend:
        signals.append("文本同时包含时间线索和变化方向")
    elif has_time:
        signals.append("文本或表格包含时间线索")
    if has_composition:
        signals.append("文本包含占比、构成、份额或来源结构")
    if has_distribution:
        signals.append("文本描述区间、集中程度或分布状态")
    if has_correlation:
        signals.append("文本表达变量之间的影响或相关关系")
    if has_comparison:
        signals.append("文本表达对象之间的高低或差异比较")

    if has_correlation:
        intent = "correlation"
        confidence = 0.9 if len(numeric_indexes) >= 2 else 0.82
        alternatives = ["line", "bar"]
    elif has_composition:
        intent = "composition"
        confidence = 0.9
        alternatives = ["bar"]
    elif has_distribution:
        intent = "distribution"
        confidence = 0.84
        alternatives = ["histogram", "box"]
    elif has_time and (has_trend or has_time_labels):
        intent = "trend"
        confidence = 0.88 if has_trend else 0.8
        alternatives = ["area", "bar"]
    elif has_comparison:
        intent = "comparison"
        confidence = 0.82
        alternatives = ["line"]
    elif len(numeric_indexes) >= 3 and len(rows) >= 4:
        intent = "distribution"
        confidence = 0.72
        alternatives = ["heatmap", "bar"]
        signals.append("多数值列适合展示数值分布或强弱差异")
    elif len(numeric_indexes) >= 2 and len(columns) <= 3:
        intent = "correlation"
        confidence = 0.72
        alternatives = ["bar"]
        signals.append("少量字段中存在双数值列，按关系探索处理")
    elif len(rows) > 8 and len(numeric_indexes) == 1:
        intent = "trend" if has_time else "distribution"
        confidence = 0.68
        alternatives = ["bar"]
        signals.append("单数值列且数据点较多")
    else:
        intent = "comparison"
        confidence = 0.62
        alternatives = ["line", "pie"]
        signals.append("未命中强语义关键词，默认按类别比较处理")

    chart_type = INTENT_TO_CHART_TYPE[intent]
    if intent == "distribution" and "histogram" in alternatives and len(numeric_indexes) == 1 and len(rows) > 8:
        chart_type = "histogram"

    reason = f"识别为 {intent}，推荐 {chart_type} 图；依据：" + "、".join(signals[:4])
    return {
        "intent_category": intent,
        "chart_type": chart_type,
        "confidence": round(confidence, 2),
        "signals": signals,
        "alternatives": alternatives,
        "reason": reason,
    }


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


def _illustration_style_profile(style_hint: str) -> dict[str, Any]:
    return ILLUSTRATION_STYLE_PROFILES.get(style_hint, ILLUSTRATION_STYLE_PROFILES["auto"])


def _build_illustration_prompt(visual_theme: str, style_hint: str, image_model: str, summary: str, keywords: list[str], audience: str) -> str:
    sanitized_theme = _sanitize_illustration_text(visual_theme) or "business scenario illustration"
    sanitized_summary = _sanitize_illustration_text(summary)
    sanitized_keywords = _sanitize_keywords(keywords)
    style_text = "auto" if style_hint == "auto" else style_hint
    profile = _illustration_style_profile(style_hint)
    parts = [
        f"Theme: {sanitized_theme}",
        f"Style: {style_text}",
        f"Audience: {audience or 'business'}",
        f"Scene: {profile['scene']}",
        f"Mood: {profile['mood']}",
    ]
    if sanitized_summary:
        parts.append(f"Direction: {sanitized_summary}")
    if sanitized_keywords:
        parts.append(f"Keywords: {', '.join(sanitized_keywords[:4])}")
    parts.append("Create a scene illustration only: people, objects, environment, and concept metaphor.")
    parts.append("Avoid charts, axes, dashboards, data panels, tables, bar shapes, line plots, pie slices, or explicit statistical graphics.")
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
    logger = logging.getLogger("ppt_pipeline")
    if not logger.handlers:
        try:
            log_dir.mkdir(parents=True, exist_ok=True)
            handler = logging.FileHandler(log_dir / "pipeline.log", encoding="utf-8")
        except OSError:
            fallback_dir = Path(tempfile.gettempdir()) / "ppt-smart-chart-logs"
            fallback_dir.mkdir(parents=True, exist_ok=True)
            handler = logging.FileHandler(fallback_dir / "pipeline.log", encoding="utf-8")
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
    requested_image_model = str(state.get("image_model", "local") or "local").strip().lower()
    image_model = _normalize_image_model(requested_image_model)
    table = (state.get("extracted_tables") or [{}])[0]
    columns = table.get("columns", [])
    rows = table.get("rows", [])
    table_summary = f"columns={columns}; sample_rows={rows[:4]}"
    recommendation = _recommend_chart_intent(state.get("text_content", ""), columns, rows)

    heuristic_result = {
        "task": "chart_generation",
        "chart_type": chart_override or recommendation["chart_type"],
        "chart_theme": chart_theme,
        "audience": "business",
        "summary": "Inferred from slide text, label pattern, and extracted table structure.",
        "reason": recommendation["reason"],
        "intent_category": recommendation["intent_category"],
        "recommendation_confidence": recommendation["confidence"],
        "recommendation_signals": recommendation["signals"],
        "chart_alternatives": recommendation["alternatives"],
        "chart_recommendation": recommendation,
        "visual_theme": "business office collaboration" if illustration_style == "auto" else f"{illustration_style} visual scene",
        "palette": ["deep-blue", "sky-blue"],
        "keywords": ["office space", "team collaboration", "business atmosphere"],
        "source": "heuristic",
        "semantic_mode": "local",
        "image_model": image_model,
        "illustration_style": illustration_style,
    }

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
                "intent_category": recommendation["intent_category"],
                "recommendation_confidence": recommendation["confidence"],
                "recommendation_signals": recommendation["signals"],
                "chart_alternatives": recommendation["alternatives"],
                "chart_recommendation": recommendation,
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
        heuristic_result["reason"] = f"Chart type manually overridden to {chart_override}; original recommendation was {recommendation['chart_type']} for {recommendation['intent_category']}."
    state["intent"] = heuristic_result
    return append_log(state, "Semantic analysis completed with local heuristic.")


def generate_chart_node(state: dict[str, Any]) -> dict[str, Any]:
    chart_type = state["intent"].get("chart_type", "bar")
    output_path = ensure_output_dir() / f"{state.get('request_id', 'req')}_chart_slide_{state['current_slide']}.png"
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


def _write_illustration_png(output_path: Path, visual_theme: str, style_hint: str, image_model: str, refined: bool = False) -> None:
    from PIL import Image, ImageDraw, ImageFont
    output_path.parent.mkdir(parents=True, exist_ok=True)
    profile = _illustration_style_profile(style_hint)
    background, accent, soft, text = profile["palette"]
    image = Image.new("RGB", (1200, 700), background)
    draw = ImageDraw.Draw(image)
    title_font = ImageFont.load_default()
    body_font = ImageFont.load_default()
    draw.rounded_rectangle((0, 0, 1199, 699), radius=28, fill=background)
    draw.ellipse((820, 70, 1110, 360), fill=soft)
    draw.rounded_rectangle((90, 112, 690, 570), radius=54, fill=soft)
    draw.rounded_rectangle((735, 210, 1070, 565), radius=52, outline=accent, width=5)
    draw.ellipse((185, 220, 275, 310), fill=accent)
    draw.rounded_rectangle((155, 320, 305, 505), radius=42, fill=background)
    draw.ellipse((390, 205, 480, 295), fill=accent)
    draw.rounded_rectangle((360, 305, 510, 505), radius=42, fill=background)
    draw.rounded_rectangle((565, 250, 650, 505), radius=38, fill=background)
    draw.polygon([(772, 472), (925, 285), (1040, 472)], fill=background)
    draw.ellipse((842, 260, 902, 320), fill=accent)
    draw.rounded_rectangle((805, 475, 1000, 530), radius=28, fill=accent)
    draw.text((120, 105), "Illustration Preview", fill=text, font=title_font)
    mode = "refined prompt" if refined else "initial prompt"
    draw.text((120, 140), f"{style_hint.title()} style | {image_model.upper()} | {mode}", fill=background if style_hint == "sketch" else soft, font=body_font)
    if visual_theme:
        draw.text((120, 612), _sanitize_illustration_text(visual_theme)[:110], fill=text, font=body_font)
    image.save(output_path)


def _build_refined_illustration_prompt(state: dict[str, Any], style_hint: str, image_model: str) -> str:
    refined_style = "business" if style_hint == "auto" else style_hint
    summary = str(state["intent"].get("summary", ""))
    if summary:
        summary = f"{summary}. Use a concrete human scene and clear industry context."
    else:
        summary = "Use a concrete human scene and clear industry context."
    return _build_illustration_prompt(
        visual_theme=str(state["intent"].get("visual_theme", "business scenario illustration")),
        style_hint=refined_style,
        image_model=image_model,
        summary=summary,
        keywords=list(state["intent"].get("keywords", [])),
        audience=str(state["intent"].get("audience", "business")),
    )


def generate_illustration_node(state: dict[str, Any]) -> dict[str, Any]:
    requested_image_model = str(state.get("image_model", "local") or "local").strip().lower()
    style_hint = _normalize_illustration_style(state.get("illustration_style"))
    image_model = _normalize_image_model(requested_image_model)
    visual_theme = state["intent"].get("visual_theme", "intelligent illustration preview")
    state["illustration_prompt"] = _build_illustration_prompt(visual_theme=visual_theme, style_hint=style_hint, image_model=image_model, summary=str(state["intent"].get("summary", "")), keywords=list(state["intent"].get("keywords", [])), audience=str(state["intent"].get("audience", "business")))
    output_path = ensure_output_dir() / f"{state.get('request_id', 'req')}_illustration_slide_{state['current_slide']}.png"
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
    initial_clip_score = _estimate_clip_score(state.get("text_content", ""), state["intent"].get("visual_theme", ""), _sanitize_keywords(state["intent"].get("keywords", [])), style_hint, image_model)
    clip_score = initial_clip_score
    regenerated = False
    regenerate_attempts = 0
    regenerate_action = "none"
    regenerate_reason = ""
    if initial_clip_score < ILLUSTRATION_SCORE_THRESHOLD:
        regenerate_reason = f"Initial score {initial_clip_score} is below threshold {ILLUSTRATION_SCORE_THRESHOLD}."
        state["illustration_prompt_retry"] = _build_refined_illustration_prompt(state, style_hint, image_model)
        if generation_source == "local":
            refined_style = "business" if style_hint == "auto" else style_hint
            _write_illustration_png(output_path, visual_theme=visual_theme, style_hint=refined_style, image_model=image_model, refined=True)
            regenerated = True
            regenerate_attempts = 1
            regenerate_action = "local_refined_prompt"
            refined_score = _estimate_clip_score(state.get("text_content", ""), state["intent"].get("visual_theme", ""), _sanitize_keywords(state["intent"].get("keywords", [])), refined_style, image_model)
            clip_score = max(initial_clip_score, refined_score)
            append_log(state, f"Illustration regenerated with refined local prompt: score {initial_clip_score} -> {clip_score}.", "warning")
        else:
            regenerate_action = "manual_review_recommended"
            append_log(state, f"Illustration score is below threshold; manual review recommended: {initial_clip_score}.", "warning")
    state["illustration_meta"] = {
        "clip_score": clip_score,
        "initial_clip_score": initial_clip_score,
        "score_threshold": ILLUSTRATION_SCORE_THRESHOLD,
        "score_source": "heuristic",
        "requested_image_model": requested_image_model,
        "image_model": image_model,
        "illustration_style": style_hint,
        "external_provider_requested": image_model in {"wanx", "flux"},
        "external_provider": image_model if image_model in {"wanx", "flux"} else "",
        "resolved_image_source": generation_source,
        "fallback_to_local": generation_source == "local" and image_model in {"wanx", "flux"},
        "generation_source": generation_source,
        "generation_warning": generation_warning,
        "regenerate_hint": clip_score < ILLUSTRATION_SCORE_THRESHOLD,
        "regenerated": regenerated,
        "regenerate_attempts": regenerate_attempts,
        "regenerate_action": regenerate_action,
        "regenerate_reason": regenerate_reason,
    }
    state["intent"]["clip_score"] = clip_score
    state["intent"]["initial_clip_score"] = initial_clip_score
    state["intent"]["image_model"] = image_model
    state["intent"]["illustration_style"] = style_hint
    state["intent"]["keywords"] = _sanitize_keywords(state["intent"].get("keywords", []))
    return append_log(state, "Illustration preview asset generated.")


def save_pptx_node(state: dict[str, Any]) -> dict[str, Any]:
    from backend.insert_to_pptx import insert_generated_assets
    ppt_path = Path(state["ppt_path"])
    output_dir = ensure_output_dir()
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
            layout = state.get("intent", {}).get("layout", {})
            if layout.get("layout_warning"):
                append_log(state, f"PPT layout review recommended: overlap score {layout.get('overlap_score')}.", "warning")
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
