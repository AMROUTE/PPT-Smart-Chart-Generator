from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

try:
    import pandas as pd
except ModuleNotFoundError:  # pragma: no cover
    pd = None

try:
    from pptx import Presentation
except ModuleNotFoundError:  # pragma: no cover
    Presentation = None


@dataclass
class ParsedSlideContent:
    slide_number: int
    text_content: str
    tables: list[dict[str, Any]]
    shapes: list[dict[str, Any]]

    def to_dict(self) -> dict[str, Any]:
        return {
            "slide_number": self.slide_number,
            "text_content": self.text_content,
            "tables": self.tables,
            "shapes": self.shapes,
        }


def normalize_header(value: str | None, index: int) -> str:
    text = (value or "").strip()
    return text or f"column_{index + 1}"


def dataframe_to_records(dataframe: pd.DataFrame) -> list[list[Any]]:
    return dataframe.where(pd.notnull(dataframe), None).values.tolist()


def table_to_dataframe(table: Any) -> pd.DataFrame:
    if pd is None:
        raise ModuleNotFoundError("pandas is required for table_to_dataframe.")

    matrix = [[cell.text.strip() for cell in row.cells] for row in table.rows]
    if not matrix:
        return pd.DataFrame()

    headers = [normalize_header(value, index) for index, value in enumerate(matrix[0])]
    deduped_headers: list[str] = []
    header_counts: dict[str, int] = {}
    for header in headers:
        count = header_counts.get(header, 0)
        deduped_headers.append(header if count == 0 else f"{header}_{count + 1}")
        header_counts[header] = count + 1

    return pd.DataFrame(matrix[1:], columns=deduped_headers)


def extract_text_from_shape(shape: Any) -> str:
    if not getattr(shape, "has_text_frame", False):
        return ""
    text = shape.text.strip()
    return text


def describe_shape(shape: Any, index: int) -> dict[str, Any]:
    shape_type = getattr(getattr(shape, "shape_type", None), "name", str(getattr(shape, "shape_type", "")))
    payload = {
        "index": index,
        "name": getattr(shape, "name", f"shape_{index}"),
        "shape_type": shape_type,
        "has_text": bool(getattr(shape, "has_text_frame", False)),
        "has_table": bool(getattr(shape, "has_table", False)),
        "left": int(getattr(shape, "left", 0)),
        "top": int(getattr(shape, "top", 0)),
        "width": int(getattr(shape, "width", 0)),
        "height": int(getattr(shape, "height", 0)),
    }
    text = extract_text_from_shape(shape)
    if text:
        payload["text"] = text
    return payload


def extract_tables(slide: Any) -> list[dict[str, Any]]:
    tables: list[dict[str, Any]] = []
    table_index = 1
    for shape in slide.shapes:
        if not getattr(shape, "has_table", False):
            continue

        dataframe = table_to_dataframe(shape.table)
        tables.append(
            {
                "title": getattr(shape, "name", f"table_{table_index}"),
                "columns": dataframe.columns.tolist(),
                "rows": dataframe_to_records(dataframe),
                "dataframe": dataframe,
            }
        )
        table_index += 1
    return tables


def extract_shapes(slide: Any) -> list[dict[str, Any]]:
    return [describe_shape(shape, index) for index, shape in enumerate(slide.shapes, start=1)]


def extract_slide_content(ppt_path: str | Path, slide_number: int) -> ParsedSlideContent:
    if Presentation is None:
        raise ModuleNotFoundError("python-pptx is required for extract_slide_content.")

    presentation_path = Path(ppt_path)
    if not presentation_path.exists():
        raise FileNotFoundError(f"PPT file not found: {presentation_path}")

    presentation = Presentation(str(presentation_path))
    if slide_number < 1 or slide_number > len(presentation.slides):
        raise ValueError(
            f"Slide number {slide_number} is out of range. This PPT has {len(presentation.slides)} slides."
        )

    slide = presentation.slides[slide_number - 1]
    tables = extract_tables(slide)
    shapes = extract_shapes(slide)
    text_blocks = [shape["text"] for shape in shapes if shape.get("text")]

    return ParsedSlideContent(
        slide_number=slide_number,
        text_content="\n".join(text_blocks),
        tables=tables,
        shapes=shapes,
    )
