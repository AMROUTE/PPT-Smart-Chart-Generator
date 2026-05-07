from __future__ import annotations

from pathlib import Path
from typing import Any

try:
    from pptx import Presentation
    from pptx.dml.color import RGBColor
    from pptx.enum.text import PP_ALIGN
    from pptx.util import Emu, Pt
except ModuleNotFoundError:  # pragma: no cover
    Presentation = None
    RGBColor = None
    PP_ALIGN = None
    Emu = None
    Pt = None


def _is_raster_image(path: str | Path) -> bool:
    return Path(path).suffix.lower() in {".png", ".jpg", ".jpeg"}


def _replace_table_region(slide: Any) -> tuple[int, int, int, int] | None:
    for shape in slide.shapes:
        if getattr(shape, "has_table", False):
            return int(shape.left), int(shape.top), int(shape.width), int(shape.height)
    return None


def _default_chart_region(slide_width: int, slide_height: int) -> tuple[int, int, int, int]:
    return (
        int(slide_width * 0.08),
        int(slide_height * 0.20),
        int(slide_width * 0.50),
        int(slide_height * 0.58),
    )


def _default_illustration_region(slide_width: int, slide_height: int) -> tuple[int, int, int, int]:
    return (
        int(slide_width * 0.62),
        int(slide_height * 0.23),
        int(slide_width * 0.27),
        int(slide_height * 0.36),
    )


def _add_textbox(
    slide: Any,
    left: int,
    top: int,
    width: int,
    height: int,
    text: str,
    font_size: int,
    bold: bool = False,
    color: tuple[int, int, int] = (32, 52, 82),
) -> None:
    box = slide.shapes.add_textbox(Emu(left), Emu(top), Emu(width), Emu(height))
    frame = box.text_frame
    frame.clear()
    paragraph = frame.paragraphs[0]
    paragraph.alignment = PP_ALIGN.LEFT
    run = paragraph.add_run()
    run.text = text
    run.font.size = Pt(font_size)
    run.font.bold = bold
    run.font.color.rgb = RGBColor(*color)


def _add_caption_box(slide: Any, left: int, top: int, width: int, height: int, text: str) -> None:
    box = slide.shapes.add_textbox(Emu(left), Emu(top), Emu(width), Emu(height))
    frame = box.text_frame
    frame.clear()
    frame.word_wrap = True
    paragraph = frame.paragraphs[0]
    run = paragraph.add_run()
    run.text = text
    run.font.size = Pt(14)
    run.font.color.rgb = RGBColor(88, 104, 127)


def insert_generated_assets(
    ppt_path: str | Path,
    output_path: str | Path,
    slide_number: int,
    chart_path: str | Path | None = None,
    illustration_path: str | Path | None = None,
    title: str = "",
    subtitle: str = "",
    intent: dict[str, Any] | None = None,
) -> Path:
    if Presentation is None:
        raise ModuleNotFoundError("python-pptx is required for PPT writeback.")

    source = Path(ppt_path)
    target = Path(output_path)
    if not source.exists():
        raise FileNotFoundError(f"PPT file not found: {source}")

    presentation = Presentation(str(source))
    if slide_number < 1 or slide_number > len(presentation.slides):
        raise ValueError(f"Slide number {slide_number} is out of range.")

    slide = presentation.slides[slide_number - 1]
    slide_width = int(presentation.slide_width)
    slide_height = int(presentation.slide_height)
    chart_region = _replace_table_region(slide) or _default_chart_region(slide_width, slide_height)
    illu_region = _default_illustration_region(slide_width, slide_height)

    summary = subtitle or "自动生成图表与配图结果"
    intent = intent or {}
    chart_type = intent.get("chart_type", "bar")
    model = intent.get("image_model", "local")
    style = intent.get("illustration_style", "auto")
    score = intent.get("clip_score")

    _add_textbox(
        slide,
        int(slide_width * 0.08),
        int(slide_height * 0.08),
        int(slide_width * 0.76),
        int(slide_height * 0.07),
        title or f"第 {slide_number} 页智能图表结果",
        24,
        bold=True,
    )
    _add_caption_box(
        slide,
        int(slide_width * 0.08),
        int(slide_height * 0.15),
        int(slide_width * 0.76),
        int(slide_height * 0.05),
        summary,
    )

    if chart_path and _is_raster_image(chart_path) and Path(chart_path).exists():
        slide.shapes.add_picture(
            str(chart_path),
            Emu(chart_region[0]),
            Emu(chart_region[1]),
            width=Emu(chart_region[2]),
            height=Emu(chart_region[3]),
        )
    else:
        _add_caption_box(
            slide,
            chart_region[0],
            chart_region[1],
            chart_region[2],
            int(slide_height * 0.12),
            "图表资源当前为预览格式，已保留推荐信息，待后续进一步渲染为位图后插入。",
        )

    legend_text = f"图表类型：{chart_type}  |  语义来源：{intent.get('source', 'local')}  |  模式：{intent.get('semantic_mode', 'local')}"
    _add_caption_box(
        slide,
        chart_region[0],
        chart_region[1] + chart_region[3] + int(slide_height * 0.02),
        chart_region[2],
        int(slide_height * 0.08),
        legend_text,
    )

    if illustration_path and _is_raster_image(illustration_path) and Path(illustration_path).exists():
        slide.shapes.add_picture(
            str(illustration_path),
            Emu(illu_region[0]),
            Emu(illu_region[1]),
            width=Emu(illu_region[2]),
            height=Emu(illu_region[3]),
        )
    else:
        _add_textbox(
            slide,
            illu_region[0],
            illu_region[1],
            illu_region[2],
            int(slide_height * 0.08),
            "配图区域",
            20,
            bold=True,
            color=(52, 82, 126),
        )
        _add_caption_box(
            slide,
            illu_region[0],
            illu_region[1] + int(slide_height * 0.08),
            illu_region[2],
            int(slide_height * 0.18),
            f"风格：{style}  |  模型：{model}\n匹配分数：{score if score is not None else '未评估'}\n主题：{intent.get('visual_theme', '智能生成配图')}",
        )

    target.parent.mkdir(parents=True, exist_ok=True)
    presentation.save(str(target))
    return target
