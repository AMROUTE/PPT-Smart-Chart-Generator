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
        "chart_type": chart_type,
        "audience": "business",
        "summary": "Inferred from slide text, label pattern, and extracted table structure.",
        "reason": "基于文本关键词、标签模式和表格结构进行规则判断。",
        "visual_theme": "科技数据分析插画",
        "palette": ["深蓝", "天蓝"],
        "keywords": ["数据", "分析", "业务"],
        "source": "heuristic",
    }
    if semantic_mode == "qwen":
        try:
            from backend.qwen_client import analyze_semantics_with_qwen

            llm_result = analyze_semantics_with_qwen(state.get("text_content", ""), table_summary)
            state["intent"] = {
                "task": "chart_generation",
                "chart_type": llm_result["chart_type"],
                "audience": llm_result["audience"],
                "summary": llm_result["title"],
                "reason": llm_result["reason"],
                "visual_theme": llm_result["visual_theme"],
                "palette": llm_result["palette"],
                "keywords": llm_result["keywords"],
                "source": "qwen",
                "model": get_settings().qwen_model,
                "semantic_mode": "qwen",
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

    state["intent"] = {
        **heuristic_result,
        "semantic_mode": "local",
    }
    return append_log(state, "Semantic analysis completed with local heuristic.")


def generate_chart_node(state: dict[str, Any]) -> dict[str, Any]:
    from backend.chart_generator import generate_chart

    chart_type = state["intent"].get("chart_type", "bar")
    output_path = (
        Path(get_settings().output_dir)
        / f"{state.get('request_id', 'req')}_chart_slide_{state['current_slide']}.png"
    )
    tables = state.get("extracted_tables", [])

    try:
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
        fallback_path = _write_chart_fallback_svg(output_path, state["current_slide"], tables)
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


def _write_chart_fallback_svg(output_path: Path, slide_number: int, tables: list[dict[str, Any]]) -> Path:
    svg_path = output_path.with_suffix(".svg")
    svg_path.parent.mkdir(parents=True, exist_ok=True)
    rows = tables[0].get("rows", [])[:4] if tables else []
    bars: list[str] = []
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
        bars.append(
            f'<rect x="{x}" y="{y}" width="84" height="{height}" rx="16" fill="#5aa3ff" />'
            f'<text x="{x + 42}" y="585" text-anchor="middle" fill="#d7ebff" font-size="18">{label}</text>'
        )
    svg_path.write_text(
        (
            '<svg xmlns="http://www.w3.org/2000/svg" width="1200" height="700" viewBox="0 0 1200 700">'
            '<rect width="1200" height="700" rx="28" fill="#132034" />'
            f'<text x="120" y="130" fill="#ffffff" font-size="42">Slide {slide_number} Chart Preview</text>'
            '<text x="120" y="182" fill="#9ac7ff" font-size="24">Fallback preview generated for local demo</text>'
            '<line x1="100" y1="540" x2="1060" y2="540" stroke="#4e6985" stroke-width="3" />'
            f'{"".join(bars)}'
            "</svg>"
        ),
        encoding="utf-8",
    )
    return svg_path


def _write_illustration_svg(output_path: Path, prompt: str) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    safe_prompt = prompt.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
    prompt_lower = prompt.lower()

    if any(keyword in prompt_lower for keyword in ["finance", "business", "revenue", "profit", "增长", "营收", "商业"]):
        accent = "#f59e0b"
        accent_two = "#38bdf8"
        motif = (
            "<rect x='160' y='250' width='120' height='220' rx='24' fill='#f59e0b' opacity='0.88' />"
            "<rect x='330' y='190' width='120' height='280' rx='24' fill='#38bdf8' opacity='0.88' />"
            "<rect x='500' y='130' width='120' height='340' rx='24' fill='#22c55e' opacity='0.88' />"
            "<path d='M180 520 C340 420, 460 420, 620 240' stroke='#ffffff' stroke-width='10' fill='none' stroke-linecap='round' />"
        )
    elif any(keyword in prompt_lower for keyword in ["medical", "health", "医疗", "医院", "患者"]):
        accent = "#fb7185"
        accent_two = "#60a5fa"
        motif = (
            "<circle cx='300' cy='280' r='92' fill='#fb7185' opacity='0.9' />"
            "<rect x='270' y='210' width='60' height='140' rx='14' fill='#ffffff' />"
            "<rect x='230' y='250' width='140' height='60' rx='14' fill='#ffffff' />"
            "<rect x='520' y='200' width='220' height='160' rx='28' fill='#60a5fa' opacity='0.88' />"
            "<path d='M550 280 H710' stroke='#ffffff' stroke-width='12' stroke-linecap='round' />"
            "<path d='M630 210 V350' stroke='#ffffff' stroke-width='12' stroke-linecap='round' />"
        )
    elif any(keyword in prompt_lower for keyword in ["education", "school", "教学", "教育", "学生"]):
        accent = "#8b5cf6"
        accent_two = "#f97316"
        motif = (
            "<path d='M200 250 L420 160 L640 250 L420 340 Z' fill='#8b5cf6' opacity='0.9' />"
            "<rect x='340' y='340' width='160' height='130' rx='20' fill='#f97316' opacity='0.88' />"
            "<path d='M640 250 V390' stroke='#ffffff' stroke-width='10' stroke-linecap='round' />"
            "<circle cx='640' cy='410' r='26' fill='#ffffff' opacity='0.95' />"
        )
    else:
        accent = "#2dd4bf"
        accent_two = "#60a5fa"
        motif = (
            "<circle cx='260' cy='250' r='110' fill='#2dd4bf' opacity='0.22' />"
            "<rect x='180' y='190' width='220' height='160' rx='32' fill='#2dd4bf' opacity='0.82' />"
            "<rect x='470' y='150' width='260' height='220' rx='36' fill='#60a5fa' opacity='0.82' />"
            "<circle cx='810' cy='220' r='70' fill='#f8fafc' opacity='0.25' />"
        )

    output_path.write_text(
        (
            '<svg xmlns="http://www.w3.org/2000/svg" width="1200" height="700" viewBox="0 0 1200 700">'
            "<defs><linearGradient id='bg' x1='0' x2='1' y1='0' y2='1'>"
            "<stop offset='0%' stop-color='#0f2742' />"
            f"<stop offset='100%' stop-color='{accent_two}' />"
            "</linearGradient></defs>"
            "<rect width='1200' height='700' fill='url(#bg)' rx='28' />"
            "<circle cx='980' cy='160' r='84' fill='rgba(255,255,255,0.08)' />"
            f"<circle cx='240' cy='180' r='110' fill='{accent}' opacity='0.14' />"
            f"{motif}"
            "<rect x='120' y='470' width='960' height='120' rx='28' fill='rgba(255,255,255,0.14)' />"
            "<text x='120' y='142' fill='#f7fbff' font-size='48'>Semantic Illustration Preview</text>"
            "<text x='120' y='205' fill='#d8ebff' font-size='28'>Topic-aware local design mock</text>"
            f"<text x='120' y='525' fill='#ffffff' font-size='24'>{safe_prompt[:90]}</text>"
            "</svg>"
        ),
        encoding="utf-8",
    )


def generate_illustration_node(state: dict[str, Any]) -> dict[str, Any]:
    topic_hint = (state.get("text_content") or "business presentation").splitlines()[0][:80]
    palette_hint = ", ".join(state["intent"].get("palette", [])[:2])
    keyword_hint = ", ".join(state["intent"].get("keywords", [])[:3])
    state["illustration_prompt"] = (
        f"{state['intent'].get('visual_theme', '科技数据分析插画')}，关键词：{keyword_hint}，主色：{palette_hint}，主题：{topic_hint}"
    )
    output_path = (
        Path(get_settings().output_dir)
        / f"{state.get('request_id', 'req')}_illustration_slide_{state['current_slide']}.svg"
    )
    _write_illustration_svg(output_path, state["illustration_prompt"])
    state["illustration_image"] = str(output_path)
    return append_log(state, "Illustration preview asset generated.")


def save_pptx_node(state: dict[str, Any]) -> dict[str, Any]:
    ppt_path = Path(state["ppt_path"])
    output_dir = Path(get_settings().output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    final_path = output_dir / f"{ppt_path.stem}_enhanced{ppt_path.suffix}"
    if ppt_path.exists():
        shutil.copyfile(ppt_path, final_path)
    else:
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
        ).to_dict()
    else:
        initial_state = dict(payload)
        initial_state.setdefault("logs", [])
        initial_state.setdefault("stage_history", [])
        initial_state.setdefault("retry_counts", {})
        initial_state.setdefault("progress", 0)
        initial_state.setdefault("status", "pending")
        initial_state.setdefault("semantic_mode", "local")

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
