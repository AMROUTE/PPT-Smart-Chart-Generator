from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

try:
    from pptx import Presentation
    from pptx.dml.color import RGBColor
    from pptx.enum.text import PP_ALIGN
    from pptx.util import Emu, Inches, Pt
except ModuleNotFoundError:  # pragma: no cover
    Presentation = None
    RGBColor = None
    PP_ALIGN = None
    Emu = None
    Inches = None
    Pt = None


@dataclass
class InsertResult:
    output_path: str
    slide_number: int
    chart_left: int
    chart_top: int
    chart_width: int
    chart_height: int
    replaced_table: bool

    def to_dict(self) -> dict[str, Any]:
        return {
            "output_path": self.output_path,
            "slide_number": self.slide_number,
            "chart_left": self.chart_left,
            "chart_top": self.chart_top,
            "chart_width": self.chart_width,
            "chart_height": self.chart_height,
            "replaced_table": self.replaced_table,
        }


def _ensure_dependencies() -> None:
    if Presentation is None:
        raise ModuleNotFoundError("python-pptx is required for PPT insertion.")


def _derive_output_path(ppt_path: str | Path, output_path: str | Path | None) -> Path:
    source = Path(ppt_path)
    return Path(output_path) if output_path is not None else source.with_name(f"{source.stem}_enhanced{source.suffix}")


def _is_raster_image(path: str | Path) -> bool:
    return Path(path).suffix.lower() in {".png", ".jpg", ".jpeg"}


def _best_anchor(shapes: list[dict[str, Any]]) -> dict[str, int]:
    table_shapes = [shape for shape in shapes if shape.get("has_table")]
    if table_shapes:
        largest = max(table_shapes, key=lambda item: item.get("width", 0) * item.get("height", 0))
        return {
            "index": int(largest.get("index", 0)),
            "left": int(largest.get("left", 0)),
            "top": int(largest.get("top", 0)),
            "width": int(largest.get("width", 0)),
            "height": int(largest.get("height", 0)),
        }
    return {"index": 0, "left": int(Inches(0.8)), "top": int(Inches(1.5)), "width": int(Inches(8.0)), "height": int(Inches(4.5))}


def _remove_shape(shape: Any) -> None:
    element = shape._element
    element.getparent().remove(element)


def _replace_table_shape(slide: Any, anchor_index: int) -> bool:
    if anchor_index <= 0:
        return False
    shapes = list(slide.shapes)
    if anchor_index > len(shapes):
        return False
    candidate = shapes[anchor_index - 1]
    if not getattr(candidate, "has_table", False):
        return False
    _remove_shape(candidate)
    return True


def _replace_table_region(slide: Any) -> tuple[int, int, int, int] | None:
    for shape in slide.shapes:
        if getattr(shape, "has_table", False):
            return int(shape.left), int(shape.top), int(shape.width), int(shape.height)
    return None


def _default_chart_region(slide_width: int, slide_height: int) -> tuple[int, int, int, int]:
    return (int(slide_width * 0.08), int(slide_height * 0.20), int(slide_width * 0.50), int(slide_height * 0.58))


def _default_illustration_region(slide_width: int, slide_height: int) -> tuple[int, int, int, int]:
    return (int(slide_width * 0.62), int(slide_height * 0.23), int(slide_width * 0.27), int(slide_height * 0.36))


def _add_textbox(slide: Any, left: int, top: int, width: int, height: int, text: str, font_size: int, bold: bool = False, color: tuple[int, int, int] = (32, 52, 82)) -> None:
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


def _add_title(slide: Any, title: str) -> None:
    _add_textbox(slide, int(Inches(0.6)), int(Inches(0.25)), int(Inches(8.0)), int(Inches(0.55)), title, 22, bold=True, color=(35, 35, 35))


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


def _add_legend(slide: Any, chart_spec: dict[str, Any], chart_top: int, chart_height: int) -> None:
    y_columns = chart_spec.get("y_columns") or []
    if not y_columns:
        return
    legend_top = chart_top + chart_height + int(Inches(0.2))
    _add_caption_box(slide, int(Inches(0.6)), legend_top, int(Inches(8.2)), int(Inches(0.8)), f"Legend: {', '.join(y_columns)}")


def insert_chart_to_pptx(ppt_path: str | Path, chart_image_path: str | Path, slide_number: int, chart_title: str, chart_spec: dict[str, Any] | None = None, shapes: list[dict[str, Any]] | None = None, output_path: str | Path | None = None) -> InsertResult:
    _ensure_dependencies()
    source_path = Path(ppt_path)
    image_path = Path(chart_image_path)
    if not source_path.exists():
        raise FileNotFoundError(f"PPT file not found: {source_path}")
    if not image_path.exists():
        raise FileNotFoundError(f"Chart image not found: {image_path}")

    presentation = Presentation(str(source_path))
    if slide_number < 1 or slide_number > len(presentation.slides):
        raise ValueError(f"Slide number {slide_number} is out of range. This PPT has {len(presentation.slides)} slides.")

    slide = presentation.slides[slide_number - 1]
    anchor = _best_anchor(shapes or [])
    replaced_table = _replace_table_shape(slide, anchor["index"])
    chart_left = anchor["left"]
    chart_top = max(anchor["top"], int(Inches(1.1)))
    chart_width = min(anchor["width"] or int(Inches(8.0)), int(Inches(8.6)))
    chart_height = min(anchor["height"] or int(Inches(4.5)), int(Inches(4.8)))

    _add_title(slide, chart_title)
    slide.shapes.add_picture(str(image_path), chart_left, chart_top, width=chart_width, height=chart_height)
    _add_legend(slide, chart_spec or {}, chart_top, chart_height)

    destination = _derive_output_path(source_path, output_path)
    destination.parent.mkdir(parents=True, exist_ok=True)
    presentation.save(str(destination))
    return InsertResult(str(destination), slide_number, int(chart_left), int(chart_top), int(chart_width), int(chart_height), replaced_table)


def insert_generated_assets(ppt_path: str | Path, output_path: str | Path, slide_number: int, chart_path: str | Path | None = None, illustration_path: str | Path | None = None, title: str = "", subtitle: str = "", intent: dict[str, Any] | None = None, shapes: list[dict[str, Any]] | None = None) -> Path:
    _ensure_dependencies()
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

    anchor = _best_anchor(shapes or [])
    replaced_table = _replace_table_shape(slide, anchor["index"])
    if shapes and anchor["index"]:
        chart_region = (anchor["left"], max(anchor["top"], int(Inches(1.1))), min(anchor["width"] or int(Inches(8.0)), int(Inches(8.6))), min(anchor["height"] or int(Inches(4.5)), int(Inches(4.8))))
    else:
        chart_region = _replace_table_region(slide) or _default_chart_region(slide_width, slide_height)
    illu_region = _default_illustration_region(slide_width, slide_height)

    summary = subtitle or "Auto-generated chart and illustration preview"
    intent = intent or {}
    chart_type = intent.get("chart_type", "bar")
    model = intent.get("image_model", "local")
    style = intent.get("illustration_style", "auto")
    score = intent.get("clip_score")

    _add_textbox(slide, int(slide_width * 0.08), int(slide_height * 0.08), int(slide_width * 0.76), int(slide_height * 0.07), title or f"Slide {slide_number} chart result", 24, bold=True)
    _add_caption_box(slide, int(slide_width * 0.08), int(slide_height * 0.15), int(slide_width * 0.76), int(slide_height * 0.05), summary)

    if chart_path and _is_raster_image(chart_path) and Path(chart_path).exists():
        slide.shapes.add_picture(str(chart_path), Emu(chart_region[0]), Emu(chart_region[1]), width=Emu(chart_region[2]), height=Emu(chart_region[3]))
    else:
        _add_caption_box(slide, chart_region[0], chart_region[1], chart_region[2], int(slide_height * 0.12), "Chart preview is not available as a raster image yet.")

    legend_text = f"Chart type: {chart_type} | Source: {intent.get('source', 'local')} | Mode: {intent.get('semantic_mode', 'local')}"
    _add_caption_box(slide, chart_region[0], chart_region[1] + chart_region[3] + int(slide_height * 0.02), chart_region[2], int(slide_height * 0.08), legend_text)

    if illustration_path and _is_raster_image(illustration_path) and Path(illustration_path).exists():
        slide.shapes.add_picture(str(illustration_path), Emu(illu_region[0]), Emu(illu_region[1]), width=Emu(illu_region[2]), height=Emu(illu_region[3]))
    else:
        _add_textbox(slide, illu_region[0], illu_region[1], illu_region[2], int(slide_height * 0.08), "Illustration Area", 20, bold=True, color=(52, 82, 126))
        _add_caption_box(slide, illu_region[0], illu_region[1] + int(slide_height * 0.08), illu_region[2], int(slide_height * 0.18), f"Style: {style} | Model: {model}\nMatch score: {score if score is not None else 'N/A'}\nTheme: {intent.get('visual_theme', 'Generated illustration preview')}")

    target.parent.mkdir(parents=True, exist_ok=True)
    presentation.save(str(target))
    return target