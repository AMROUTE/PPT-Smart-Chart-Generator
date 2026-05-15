from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

try:
    from pptx import Presentation
    from pptx.dml.color import RGBColor
    from pptx.enum.text import PP_ALIGN
    from pptx.util import Inches, Pt
except ModuleNotFoundError:  # pragma: no cover
    Presentation = None
    RGBColor = None
    PP_ALIGN = None
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
    if output_path is not None:
        return Path(output_path)
    return source.with_name(f"{source.stem}_enhanced{source.suffix}")


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
    return {
        "index": 0,
        "left": Inches(0.8),
        "top": Inches(1.5),
        "width": Inches(8.0),
        "height": Inches(4.5),
    }


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


def _add_title(slide: Any, title: str) -> None:
    title_box = slide.shapes.add_textbox(Inches(0.6), Inches(0.25), Inches(8.0), Inches(0.55))
    paragraph = title_box.text_frame.paragraphs[0]
    paragraph.text = title
    paragraph.alignment = PP_ALIGN.LEFT
    paragraph.font.size = Pt(22)
    paragraph.font.bold = True
    if RGBColor is not None:
        paragraph.font.color.rgb = RGBColor(35, 35, 35)


def _add_legend(slide: Any, chart_spec: dict[str, Any], chart_top: int, chart_height: int) -> None:
    y_columns = chart_spec.get("y_columns") or []
    if not y_columns:
        return

    legend_top = chart_top + chart_height + Inches(0.2)
    legend_box = slide.shapes.add_textbox(Inches(0.6), legend_top, Inches(8.2), Inches(0.8))
    frame = legend_box.text_frame
    frame.text = f"Legend: {', '.join(y_columns)}"
    paragraph = frame.paragraphs[0]
    paragraph.font.size = Pt(12)
    if RGBColor is not None:
        paragraph.font.color.rgb = RGBColor(75, 85, 99)


def insert_chart_to_pptx(
    ppt_path: str | Path,
    chart_image_path: str | Path,
    slide_number: int,
    chart_title: str,
    chart_spec: dict[str, Any] | None = None,
    shapes: list[dict[str, Any]] | None = None,
    output_path: str | Path | None = None,
) -> InsertResult:
    _ensure_dependencies()

    source_path = Path(ppt_path)
    image_path = Path(chart_image_path)
    if not source_path.exists():
        raise FileNotFoundError(f"PPT file not found: {source_path}")
    if not image_path.exists():
        raise FileNotFoundError(f"Chart image not found: {image_path}")

    presentation = Presentation(str(source_path))
    if slide_number < 1 or slide_number > len(presentation.slides):
        raise ValueError(
            f"Slide number {slide_number} is out of range. This PPT has {len(presentation.slides)} slides."
        )

    slide = presentation.slides[slide_number - 1]
    anchor = _best_anchor(shapes or [])
    replaced_table = _replace_table_shape(slide, anchor["index"])

    chart_left = anchor["left"]
    chart_top = max(anchor["top"], Inches(1.1))
    chart_width = min(anchor["width"] or Inches(8.0), Inches(8.6))
    chart_height = min(anchor["height"] or Inches(4.5), Inches(4.8))

    _add_title(slide, chart_title)
    slide.shapes.add_picture(str(image_path), chart_left, chart_top, width=chart_width, height=chart_height)
    _add_legend(slide, chart_spec or {}, chart_top, chart_height)

    destination = _derive_output_path(source_path, output_path)
    destination.parent.mkdir(parents=True, exist_ok=True)
    presentation.save(str(destination))

    return InsertResult(
        output_path=str(destination),
        slide_number=slide_number,
        chart_left=int(chart_left),
        chart_top=int(chart_top),
        chart_width=int(chart_width),
        chart_height=int(chart_height),
        replaced_table=replaced_table,
    )