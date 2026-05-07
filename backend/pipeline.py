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


PIPELINE_NODES = [
    "parse_ppt",
    "semantic_analysis",
    "generate_chart",
    "generate_illustration",
    "save_pptx",
]


STEP_PROGRESS = {
    "parse_ppt": 20,
    "semantic_analysis": 40,
    "generate_chart": 65,
    "generate_illustration": 85,
    "save_pptx": 100,
}

ILLUSTRATION_FORBIDDEN_TERMS = {
    "图表",
    "图形",
    "图示",
    "图像化数据",
    "数据看板",
    "看板",
    "坐标轴",
    "柱状图",
    "折线图",
    "饼图",
    "散点图",
    "热力图",
    "箱线图",
    "面积图",
    "直方图",
    "chart",
    "charts",
    "graph",
    "graphs",
    "dashboard",
    "bar",
    "line",
    "pie",
    "scatter",
    "heatmap",
}


def _normalize_chart_override(chart_type: str | None) -> str:
    normalized = (chart_type or "").strip().lower()
    return normalized if normalized in {"bar", "line", "pie", "scatter", "area", "histogram", "box", "heatmap"} else ""


def _normalize_illustration_style(style: str | None) -> str:
    normalized = (style or "auto").strip().lower()
    return normalized if normalized in {"auto", "business", "tech", "education", "medical", "academic", "sketch"} else "auto"


def _normalize_image_model(model: str | None) -> str:
    normalized = (model or "local").strip().lower()
    return normalized if normalized in {"local", "flux", "wanx"} else "local"


def _sanitize_illustration_text(text: str) -> str:
    sanitized = text or ""
    for term in ILLUSTRATION_FORBIDDEN_TERMS:
        sanitized = sanitized.replace(term, "")
        sanitized = sanitized.replace(term.title(), "")
        sanitized = sanitized.replace(term.upper(), "")
    sanitized = " ".join(part for part in sanitized.split() if part.strip())
    return sanitized.strip("，,、;； ")


def _sanitize_keywords(keywords: list[str]) -> list[str]:
    sanitized: list[str] = []
    for keyword in keywords:
        cleaned = _sanitize_illustration_text(str(keyword))
        if cleaned and cleaned not in sanitized:
            sanitized.append(cleaned)
    return sanitized


def _build_illustration_prompt(
    visual_theme: str,
    style_hint: str,
    image_model: str,
    summary: str,
    keywords: list[str],
    audience: str,
) -> str:
    sanitized_theme = _sanitize_illustration_text(visual_theme) or "业务主题场景插画"
    sanitized_summary = _sanitize_illustration_text(summary)
    sanitized_keywords = _sanitize_keywords(keywords)
    style_text = "自动" if style_hint == "auto" else style_hint
    parts = [
        f"主题：{sanitized_theme}",
        f"风格：{style_text}",
        f"受众：{audience or 'business'}",
    ]
    if sanitized_summary:
        parts.append(f"内容方向：{sanitized_summary}")
    if sanitized_keywords:
        parts.append(f"元素关键词：{'、'.join(sanitized_keywords[:4])}")
    parts.append("要求：仅描述人物、空间、物件、行业氛围与场景，不要出现图表、图形、坐标轴、数据看板或任何统计图元素。")
    parts.append(f"调用模型：{image_model}")
    return "；".join(parts)


def _estimate_clip_score(text_content: str, visual_theme: str, keywords: list[str], style: str, image_model: str) -> float:
    base = 6.2
    text_lower = text_content.lower()
    if any(keyword.lower() in text_lower for keyword in keywords):
        base += 0.6
    if any(marker in text_lower for marker in ["增长", "趋势", "营收", "占比", "教育", "医疗", "tech", "business"]):
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
        state["extracted_tables"] = [
            {
                "title": table["title"],
                "columns": table["columns"],
                "rows": table["rows"],
            }
            for table in parsed.tables
        ]
        state["shapes"] = parsed.shapes
        if not state["extracted_tables"]:
            raise ValueError("No table found in slide content.")
        return append_log(state, "PPT parsing completed from source file.")
    except Exception as exc:
        state["text_content"] = f"Parsed slide {state['current_slide']} from {ppt_path.name}"
        state["extracted_tables"] = [
            {
                "title": "sample_table",
                "columns": ["category", "value"],
                "rows": [["Q1", 120], ["Q2", 180], ["Q3", 156]],
            }
        ]
        state["shapes"] = []
        append_log(state, f"PPT parser fallback enabled: {exc}", "warning")
        return append_log(state, "PPT parsing fallback completed.")


def semantic_analysis_node(state: dict[str, Any]) -> dict[str, Any]:
    semantic_mode = str(state.get("semantic_mode", "local")).strip().lower() or "local"
    chart_override = _normalize_chart_override(state.get("chart_type_override"))
    illustration_style = _normalize_illustration_style(state.get("illustration_style"))
    image_model = _normalize_image_model(state.get("image_model"))
    text_content = (state.get("text_content") or "").lower()
    table = (state.get("extracted_tables") or [{}])[0]
    columns = table.get("columns", [])
    rows = table.get("rows", [])

    table_summary = f"columns={columns}; sample_rows={rows[:4]}"

    def looks_like_time_label(value: Any) -> bool:
        text = str(value)
        markers = ["q1", "q2", "q3", "q4", "202", "月", "季度", "week", "wk", "jan", "feb", "mar"]
        return any(marker in text.lower() for marker in markers)

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

    if any(keyword in text_content for keyword in ["比例", "占比", "份额", "构成", "share", "portion"]):
        chart_type = "pie"
    elif any(keyword in text_content for keyword in ["趋势", "增长", "变化", "走势", "trend", "growth"]):
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

    heuristic_result = {
        "task": "chart_generation",
        "chart_type": chart_override or chart_type,
        "audience": "business",
        "summary": "Inferred from slide text, label pattern, and extracted table structure.",
        "reason": "基于文本关键词、标签模式和表格结构进行规则判断。",
        "visual_theme": "商务办公人物场景" if illustration_style == "auto" else f"{illustration_style} 场景配图",
        "palette": ["深蓝", "天蓝"],
        "keywords": ["办公空间", "人物协作", "业务氛围"],
        "source": "heuristic",
        "semantic_mode": "local",
        "image_model": image_model,
        "illustration_style": illustration_style,
    }
    if semantic_mode == "qwen":
        try:
            from backend.qwen_client import analyze_semantics_with_qwen

            llm_result = analyze_semantics_with_qwen(
                state.get("text_content", ""),
                table_summary,
                api_key=str(state.get("custom_qwen_api_key", "") or ""),
                model=str(state.get("custom_qwen_model", "") or ""),
            )
            state["intent"] = {
                "task": "chart_generation",
                "chart_type": chart_override or llm_result["chart_type"],
                "audience": llm_result["audience"],
                "summary": llm_result["title"],
                "reason": llm_result["reason"] if not chart_override else f"用户手动指定图表类型为 {chart_override}，保留千问语义分析结果。",
                "visual_theme": llm_result["visual_theme"] if illustration_style == "auto" else f"{illustration_style} 场景配图",
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
            state["intent"] = {
                **heuristic_result,
                "reason": f"千问调用失败，已回退本地规则：{exc}",
                "semantic_mode": "local",
            }
            append_log(state, f"Qwen semantic analysis unavailable, fallback to heuristic: {exc}", "warning")
            return append_log(state, "Semantic analysis completed with heuristic fallback.")

    if chart_override:
        heuristic_result["reason"] = f"用户手动指定图表类型为 {chart_override}，已覆盖自动推荐。"
    state["intent"] = heuristic_result
    return append_log(state, "Semantic analysis completed with local heuristic.")


def generate_chart_node(state: dict[str, Any]) -> dict[str, Any]:
    chart_type = state["intent"].get("chart_type", "bar")
    output_path = (
        Path(get_settings().output_dir)
        / f"{state.get('request_id', 'req')}_chart_slide_{state['current_slide']}.png"
    )
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
        chart = generate_chart(
            records,
            chart_type=chart_type,
            output_path=output_path,
            title=title,
        )
        state["chart_spec"] = chart.to_dict()
        state["chart_image"] = chart.output_path
        return append_log(state, "Chart generation completed from extracted table.")
    except Exception as exc:
        fallback_path = _write_chart_fallback_png(output_path, state["current_slide"], tables, chart_type)
        state["chart_spec"] = {
            "chart_type": chart_type,
            "output_path": str(fallback_path),
            "title": f"Slide {state['current_slide']} chart recommendation",
            "data_points": len(tables[0].get("rows", [])) if tables else 0,
            "fallback": True,
        }
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

    points: list[tuple[int, int]] = []
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
        points.append((x + 42, y))
        draw.text((x + 10, 560), label, fill="#d7ebff", font=body_font)
        if chart_type in {"bar", "histogram"}:
            draw.rounded_rectangle((x, y, x + 84, 540), radius=16, fill="#5aa3ff")
        elif chart_type == "scatter":
            draw.ellipse((x + 26, y - 16, x + 58, y + 16), fill="#5aa3ff")
        elif chart_type == "line":
            draw.ellipse((x + 32, y - 10, x + 52, y + 10), fill="#8dd6ff")

    if chart_type == "line" and points:
        draw.line(points, fill="#8dd6ff", width=8)
    elif chart_type == "area" and points:
        polygon = [(points[0][0], 540), *points, (points[-1][0], 540)]
        draw.polygon(polygon, fill="#467fb4", outline="#8dd6ff")
    elif chart_type == "pie":
        bbox = (210, 180, 510, 480)
        colors = ["#5aa3ff", "#38bdf8", "#22c55e", "#f59e0b"]
        total = sum(float(row[1]) if len(row) > 1 else 0 for row in rows) or 1
        start = -90
        for index, row in enumerate(rows):
            value = float(row[1]) if len(row) > 1 else 0
            extent = 360 * value / total
            draw.pieslice(bbox, start=start, end=start + extent, fill=colors[index % len(colors)])
            start += extent
    elif chart_type == "heatmap":
        colors = ["#dbeafe", "#93c5fd", "#60a5fa", "#3b82f6", "#1d4ed8", "#1e3a8a"]
        idx = 0
        for row_index in range(2):
            for col_index in range(3):
                left = 180 + col_index * 120
                top = 210 + row_index * 100
                draw.rectangle((left, top, left + 120, top + 100), fill=colors[idx])
                idx += 1
    elif chart_type == "box":
        draw.rectangle((200, 260, 310, 380), outline="#8dd6ff", width=8)
        draw.line((255, 200, 255, 260), fill="#8dd6ff", width=8)
        draw.line((255, 380, 255, 460), fill="#8dd6ff", width=8)
        draw.line((210, 320, 300, 320), fill="#8dd6ff", width=8)
        draw.rectangle((420, 230, 530, 380), outline="#38bdf8", width=8)
        draw.line((475, 180, 475, 230), fill="#38bdf8", width=8)
        draw.line((475, 380, 475, 470), fill="#38bdf8", width=8)
        draw.line((430, 300, 520, 300), fill="#38bdf8", width=8)

    image.save(png_path)
    return png_path


def _write_illustration_png(
    output_path: Path,
    visual_theme: str,
    style_hint: str,
    image_model: str,
) -> None:
    from PIL import Image, ImageDraw, ImageFont

    output_path.parent.mkdir(parents=True, exist_ok=True)
    theme_lower = visual_theme.lower()
    header = "Illustration Preview"
    subheader = f"{style_hint.title()} style · {image_model.upper()}"

    if style_hint == "business" or any(keyword in theme_lower for keyword in ["business", "finance", "商业", "营收"]):
        accent = "#f59e0b"
        accent_two = "#38bdf8"
        motif = (
            "<rect x='120' y='170' width='420' height='290' rx='34' fill='rgba(255,255,255,0.08)' />"
            "<rect x='170' y='280' width='84' height='170' rx='20' fill='#f59e0b' />"
            "<rect x='290' y='230' width='84' height='220' rx='20' fill='#38bdf8' />"
            "<rect x='410' y='185' width='84' height='265' rx='20' fill='#22c55e' />"
            "<path d='M170 470 C250 430, 330 390, 452 250' stroke='#f8fafc' stroke-width='12' fill='none' stroke-linecap='round' />"
            "<circle cx='452' cy='250' r='16' fill='#f8fafc' />"
            "<rect x='690' y='200' width='240' height='170' rx='30' fill='rgba(255,255,255,0.12)' />"
            "<rect x='730' y='242' width='160' height='18' rx='9' fill='rgba(255,255,255,0.72)' />"
            "<rect x='730' y='280' width='116' height='18' rx='9' fill='rgba(255,255,255,0.44)' />"
            "<rect x='730' y='318' width='138' height='18' rx='9' fill='rgba(255,255,255,0.44)' />"
        )
    elif style_hint == "medical" or any(keyword in theme_lower for keyword in ["medical", "health", "医疗", "医院"]):
        accent = "#fb7185"
        accent_two = "#60a5fa"
        motif = (
            "<circle cx='260' cy='290' r='110' fill='rgba(255,255,255,0.10)' />"
            "<circle cx='260' cy='290' r='78' fill='#fb7185' />"
            "<rect x='232' y='215' width='56' height='150' rx='16' fill='#ffffff' />"
            "<rect x='185' y='262' width='150' height='56' rx='16' fill='#ffffff' />"
            "<rect x='470' y='190' width='230' height='290' rx='34' fill='rgba(255,255,255,0.12)' />"
            "<path d='M520 250 H650' stroke='#dbeafe' stroke-width='14' stroke-linecap='round' />"
            "<path d='M520 310 H650' stroke='#dbeafe' stroke-width='14' stroke-linecap='round' />"
            "<path d='M520 370 H610' stroke='#dbeafe' stroke-width='14' stroke-linecap='round' />"
            "<rect x='790' y='215' width='140' height='220' rx='70' fill='rgba(255,255,255,0.16)' />"
            "<path d='M860 235 V415' stroke='#ffffff' stroke-width='12' stroke-linecap='round' />"
        )
    elif style_hint in {"education", "academic"} or any(keyword in theme_lower for keyword in ["education", "school", "教学", "教育", "学术"]):
        accent = "#8b5cf6"
        accent_two = "#f97316"
        motif = (
            "<path d='M160 260 L390 160 L620 260 L390 360 Z' fill='#8b5cf6' opacity='0.95' />"
            "<rect x='292' y='360' width='196' height='104' rx='18' fill='#f8fafc' opacity='0.16' />"
            "<rect x='724' y='170' width='150' height='210' rx='24' fill='rgba(255,255,255,0.14)' />"
            "<rect x='748' y='200' width='102' height='132' rx='10' fill='#f8fafc' opacity='0.88' />"
            "<path d='M748 248 H850' stroke='#f97316' stroke-width='8' />"
            "<path d='M748 284 H850' stroke='#8b5cf6' stroke-width='8' />"
            "<path d='M748 320 H824' stroke='#38bdf8' stroke-width='8' />"
            "<circle cx='928' cy='246' r='54' fill='rgba(255,255,255,0.18)' />"
            "<path d='M915 232 L942 259 L980 205' stroke='#ffffff' stroke-width='10' fill='none' stroke-linecap='round' stroke-linejoin='round' />"
        )
    elif style_hint == "sketch":
        accent = "#94a3b8"
        accent_two = "#64748b"
        motif = (
            "<rect x='150' y='180' width='320' height='250' rx='28' fill='rgba(255,255,255,0.06)' stroke='#e2e8f0' stroke-width='5' stroke-dasharray='14 10' />"
            "<path d='M220 390 C290 250, 370 320, 420 210' stroke='#f8fafc' stroke-width='8' fill='none' stroke-linecap='round' stroke-dasharray='10 12' />"
            "<circle cx='260' cy='250' r='32' fill='none' stroke='#f8fafc' stroke-width='5' stroke-dasharray='12 10' />"
            "<rect x='560' y='205' width='280' height='180' rx='26' fill='rgba(255,255,255,0.05)' stroke='#f8fafc' stroke-width='4' stroke-dasharray='10 8' />"
            "<path d='M600 255 H790' stroke='#f8fafc' stroke-width='8' stroke-linecap='round' stroke-dasharray='10 14' />"
            "<path d='M600 302 H744' stroke='#f8fafc' stroke-width='8' stroke-linecap='round' stroke-dasharray='10 14' />"
            "<path d='M600 349 H770' stroke='#f8fafc' stroke-width='8' stroke-linecap='round' stroke-dasharray='10 14' />"
        )
    else:
        accent = "#2dd4bf"
        accent_two = "#60a5fa"
        motif = "tech"

    image = Image.new("RGB", (1200, 700), "#183250")
    draw = ImageDraw.Draw(image)
    title_font = ImageFont.load_default()
    body_font = ImageFont.load_default()
    draw.rounded_rectangle((0, 0, 1199, 699), radius=28, fill="#183250")
    draw.text((120, 110), header, fill="#f7fbff", font=title_font)
    draw.text((120, 145), subheader, fill="#d8ebff", font=body_font)

    if style_hint == "business" or any(keyword in theme_lower for keyword in ["business", "finance", "商业", "营收"]):
        draw.rounded_rectangle((120, 170, 540, 460), radius=34, outline="#f59e0b", width=3)
        draw.rounded_rectangle((170, 280, 254, 450), radius=20, fill="#f59e0b")
        draw.rounded_rectangle((290, 230, 374, 450), radius=20, fill="#38bdf8")
        draw.rounded_rectangle((410, 185, 494, 450), radius=20, fill="#22c55e")
        draw.line((170, 470, 250, 430, 330, 390, 452, 250), fill="#f8fafc", width=12)
        draw.ellipse((436, 234, 468, 266), fill="#f8fafc")
    elif style_hint == "medical" or any(keyword in theme_lower for keyword in ["medical", "health", "医疗", "医院"]):
        draw.ellipse((150, 180, 370, 400), fill="#fb7185")
        draw.rectangle((232, 215, 288, 365), fill="#ffffff")
        draw.rectangle((185, 262, 335, 318), fill="#ffffff")
        draw.rounded_rectangle((470, 190, 700, 480), radius=34, outline="#60a5fa", width=4)
        draw.line((520, 250, 650, 250), fill="#dbeafe", width=14)
        draw.line((520, 310, 650, 310), fill="#dbeafe", width=14)
        draw.line((520, 370, 610, 370), fill="#dbeafe", width=14)
    elif style_hint in {"education", "academic"} or any(keyword in theme_lower for keyword in ["education", "school", "教学", "教育", "学术"]):
        draw.polygon((160, 260, 390, 160, 620, 260, 390, 360), fill="#8b5cf6")
        draw.rounded_rectangle((724, 170, 874, 380), radius=24, outline="#f8fafc", width=3)
        draw.rectangle((748, 200, 850, 332), fill="#f8fafc")
        draw.line((748, 248, 850, 248), fill="#f97316", width=8)
        draw.line((748, 284, 850, 284), fill="#8b5cf6", width=8)
        draw.line((748, 320, 824, 320), fill="#38bdf8", width=8)
    elif style_hint == "sketch":
        draw.rounded_rectangle((150, 180, 470, 430), radius=28, outline="#e2e8f0", width=4)
        draw.line((220, 390, 290, 250, 370, 320, 420, 210), fill="#f8fafc", width=6)
        draw.rounded_rectangle((560, 205, 840, 385), radius=26, outline="#f8fafc", width=3)
        draw.line((600, 255, 790, 255), fill="#f8fafc", width=6)
        draw.line((600, 302, 744, 302), fill="#f8fafc", width=6)
        draw.line((600, 349, 770, 349), fill="#f8fafc", width=6)
    else:
        draw.rounded_rectangle((120, 170, 430, 480), radius=44, outline="#2dd4bf", width=3)
        draw.ellipse((171, 221, 379, 429), outline="#2dd4bf", width=4)
        draw.line((205, 362, 260, 240, 322, 322, 380, 214), fill="#ecfeff", width=10)
        draw.rounded_rectangle((520, 185, 850, 305), radius=30, outline="#60a5fa", width=3)
        draw.rounded_rectangle((520, 330, 850, 450), radius=30, outline="#60a5fa", width=3)

    image.save(output_path)


def generate_illustration_node(state: dict[str, Any]) -> dict[str, Any]:
    style_hint = _normalize_illustration_style(state.get("illustration_style"))
    image_model = _normalize_image_model(state.get("image_model"))
    visual_theme = state["intent"].get("visual_theme", "智能配图预览")
    state["illustration_prompt"] = _build_illustration_prompt(
        visual_theme=visual_theme,
        style_hint=style_hint,
        image_model=image_model,
        summary=str(state["intent"].get("summary", "")),
        keywords=list(state["intent"].get("keywords", [])),
        audience=str(state["intent"].get("audience", "business")),
    )
    output_path = (
        Path(get_settings().output_dir)
        / f"{state.get('request_id', 'req')}_illustration_slide_{state['current_slide']}.png"
    )
    generation_source = "local"
    generation_warning = ""
    if image_model in {"wanx", "flux"}:
        try:
            from backend.image_clients import generate_flux_image, generate_wanx_image

            if image_model == "wanx":
                generate_wanx_image(
                    state["illustration_prompt"],
                    output_path,
                    api_key=str(state.get("custom_wanx_api_key", "") or ""),
                )
            else:
                generate_flux_image(
                    state["illustration_prompt"],
                    output_path,
                    api_key=str(state.get("custom_flux_api_key", "") or ""),
                )
            generation_source = image_model
            append_log(state, f"Illustration generated through {image_model.upper()} API.")
        except Exception as exc:
            generation_warning = str(exc)
            append_log(state, f"{image_model.upper()} illustration fallback enabled: {exc}", "warning")

    if generation_source == "local":
        _write_illustration_png(
            output_path,
            visual_theme=visual_theme,
            style_hint=style_hint,
            image_model=image_model,
        )

    state["illustration_image"] = str(output_path)
    clip_score = _estimate_clip_score(
        state.get("text_content", ""),
        state["intent"].get("visual_theme", ""),
        _sanitize_keywords(state["intent"].get("keywords", [])),
        style_hint,
        image_model,
    )
    state["illustration_meta"] = {
        "clip_score": clip_score,
        "score_source": "heuristic",
        "image_model": image_model,
        "illustration_style": style_hint,
        "generation_source": generation_source,
        "generation_warning": generation_warning,
        "regenerate_hint": clip_score < 6.5,
    }
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
    final_path = output_dir / f"{ppt_path.stem}_enhanced{ppt_path.suffix}"

    if ppt_path.exists():
        summary = state["intent"].get("reason") or "自动生成结果"
        try:
            insert_generated_assets(
                ppt_path=ppt_path,
                output_path=final_path,
                slide_number=state["current_slide"],
                chart_path=state.get("chart_image") or None,
                illustration_path=state.get("illustration_image") or None,
                title=f"第 {state['current_slide']} 页图表增强结果",
                subtitle=summary,
                intent=state.get("intent", {}),
            )
            state["final_pptx_path"] = str(final_path)
            return append_log(state, "Enhanced PPT saved with inserted chart assets.")
        except Exception as exc:
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
        return "\n".join(
            [
                "graph TD",
                "    start([Start]) --> parse_ppt",
                "    parse_ppt --> semantic_analysis",
                "    semantic_analysis --> generate_chart",
                "    generate_chart --> generate_illustration",
                "    generate_illustration --> save_pptx",
                "    save_pptx --> end([End])",
            ]
        )


def build_pipeline():
    node_pairs = [
        ("parse_ppt", parse_ppt_node),
        ("semantic_analysis", semantic_analysis_node),
        ("generate_chart", generate_chart_node),
        ("generate_illustration", generate_illustration_node),
        ("save_pptx", save_pptx_node),
    ]
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
    state["stage_history"].append(
        {
            "stage": stage_name,
            "status": status,
            "details": details,
            "progress": STEP_PROGRESS.get(stage_name, state.get("progress", 0)),
            "timestamp": datetime.now().isoformat(timespec="seconds"),
        }
    )


def _run_step_with_retry(
    state: dict[str, Any],
    step_name: str,
    step_fn: Any,
    max_retries: int,
) -> dict[str, Any]:
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
        initial_state = AgentState(
            ppt_path=payload.ppt_path,
            request_id=payload.request_id,
            current_slide=payload.current_slide,
            semantic_mode=payload.semantic_mode,
            chart_type_override=payload.chart_type_override,
            illustration_style=payload.illustration_style,
            image_model=payload.image_model,
        ).to_dict()
    else:
        initial_state = dict(payload)
        initial_state.setdefault("logs", [])
        initial_state.setdefault("stage_history", [])
        initial_state.setdefault("retry_counts", {})
        initial_state.setdefault("progress", 0)
        initial_state.setdefault("status", "pending")
        initial_state.setdefault("semantic_mode", "local")
        initial_state.setdefault("chart_type_override", "")
        initial_state.setdefault("illustration_style", "auto")
        initial_state.setdefault("image_model", "local")

    state = dict(initial_state)
    state["status"] = "running"
    append_log(state, "Pipeline execution started.")
    for step_name, step_fn in [
        ("parse_ppt", parse_ppt_node),
        ("semantic_analysis", semantic_analysis_node),
        ("generate_chart", generate_chart_node),
        ("generate_illustration", generate_illustration_node),
        ("save_pptx", save_pptx_node),
    ]:
        state = _run_step_with_retry(state, step_name, step_fn, get_settings().max_retries)
    state["status"] = "completed"
    append_log(state, "Pipeline execution completed.")
    return state


def export_pipeline_mermaid() -> str:
    return get_pipeline_app().get_graph().draw_mermaid()
