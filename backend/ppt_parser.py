from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import re
from typing import Any

from PIL import Image, ImageDraw, ImageFont

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


@dataclass
class SlidePreview:
    slide_number: int
    slide_count: int
    output_path: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "slide_number": self.slide_number,
            "slide_count": self.slide_count,
            "output_path": self.output_path,
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

    normalized_matrix: list[list[str]] = []
    for row_index, row in enumerate(matrix):
        filled_row: list[str] = []
        for col_index, value in enumerate(row):
            normalized = value
            if not normalized and col_index > 0:
                normalized = filled_row[col_index - 1]
            if not normalized and row_index > 0:
                normalized = normalized_matrix[row_index - 1][col_index]
            filled_row.append(normalized)
        normalized_matrix.append(filled_row)

    headers = [normalize_header(value, index) for index, value in enumerate(normalized_matrix[0])]
    deduped_headers: list[str] = []
    header_counts: dict[str, int] = {}
    for header in headers:
        count = header_counts.get(header, 0)
        deduped_headers.append(header if count == 0 else f"{header}_{count + 1}")
        header_counts[header] = count + 1

    return pd.DataFrame(normalized_matrix[1:], columns=deduped_headers)


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
        raw_matrix = [[cell.text.strip() for cell in row.cells] for row in shape.table.rows]
        merged_hints = []
        for row_index, row in enumerate(raw_matrix):
            for col_index, value in enumerate(row):
                if value:
                    continue
                if col_index > 0 and row[col_index - 1]:
                    merged_hints.append(
                        {
                            "row": row_index,
                            "col": col_index,
                            "merge_origin": [row_index, col_index - 1],
                            "direction": "horizontal",
                        }
                    )
                elif row_index > 0 and raw_matrix[row_index - 1][col_index]:
                    merged_hints.append(
                        {
                            "row": row_index,
                            "col": col_index,
                            "merge_origin": [row_index - 1, col_index],
                            "direction": "vertical",
                        }
                    )

        tables.append(
            {
                "title": getattr(shape, "name", f"table_{table_index}"),
                "columns": dataframe.columns.tolist(),
                "rows": dataframe_to_records(dataframe),
                "dataframe": dataframe,
                "merge_hints": merged_hints,
                "raw_matrix": raw_matrix,
            }
        )
        table_index += 1
    return tables


def extract_shapes(slide: Any) -> list[dict[str, Any]]:
    return [describe_shape(shape, index) for index, shape in enumerate(slide.shapes, start=1)]


def infer_table_from_text_blocks(text_blocks: list[str]) -> list[dict[str, Any]]:
    joined = "\n".join(text_blocks)
    matches = re.findall(
        r"([A-Za-z\u4e00-\u9fff][A-Za-z0-9\u4e00-\u9fff\s]{0,24})[:：]\s*(-?\d+(?:\.\d+)?)",
        joined,
    )
    if not matches:
        matches = re.findall(
            r"((?:20\d{2}|Q[1-4]|一季度|二季度|三季度|四季度|[1-9]|1[0-2]月))\s*[：:,-]?\s*(-?\d+(?:\.\d+)?)",
            joined,
        )
    if not matches:
        return []
    return [
        {
            "title": "text_inferred_table",
            "columns": ["category", "value"],
            "rows": [[label.strip(), float(value)] for label, value in matches],
            "merge_hints": [],
            "raw_matrix": [["category", "value"], *[[label.strip(), value] for label, value in matches]],
        }
    ]


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
    if not tables:
        tables = infer_table_from_text_blocks(text_blocks)

    return ParsedSlideContent(
        slide_number=slide_number,
        text_content="\n".join(text_blocks),
        tables=tables,
        shapes=shapes,
    )


def get_slide_count(ppt_path: str | Path) -> int:
    if Presentation is None:
        raise ModuleNotFoundError("python-pptx is required for get_slide_count.")
    presentation_path = Path(ppt_path)
    presentation = Presentation(str(presentation_path))
    return len(presentation.slides)


def render_slide_preview(ppt_path: str | Path, slide_number: int, output_path: str | Path) -> SlidePreview:
    if Presentation is None:
        raise ModuleNotFoundError("python-pptx is required for render_slide_preview.")

    presentation_path = Path(ppt_path)
    if not presentation_path.exists():
        raise FileNotFoundError(f"PPT file not found: {presentation_path}")

    presentation = Presentation(str(presentation_path))
    slide_count = len(presentation.slides)
    if slide_number < 1 or slide_number > slide_count:
        raise ValueError(f"Slide number {slide_number} is out of range. This PPT has {slide_count} slides.")

    slide = presentation.slides[slide_number - 1]
    slide_width = int(presentation.slide_width) or 1
    slide_height = int(presentation.slide_height) or 1
    canvas_width = 1280
    canvas_height = max(720, int(canvas_width * slide_height / slide_width))
    scale_x = canvas_width / slide_width
    scale_y = canvas_height / slide_height

    image = Image.new("RGB", (canvas_width, canvas_height), "#f8fbff")
    draw = ImageDraw.Draw(image)
    title_font = ImageFont.load_default()
    body_font = ImageFont.load_default()

    draw.rounded_rectangle((20, 20, canvas_width - 20, canvas_height - 20), radius=28, outline="#c6d7ea", width=3)

    for shape in slide.shapes:
        left = int(getattr(shape, "left", 0) * scale_x)
        top = int(getattr(shape, "top", 0) * scale_y)
        width = max(18, int(getattr(shape, "width", 0) * scale_x))
        height = max(18, int(getattr(shape, "height", 0) * scale_y))
        box = (left, top, left + width, top + height)

        if getattr(shape, "has_table", False):
            draw.rounded_rectangle(box, radius=18, fill="#ffffff", outline="#3b82f6", width=3)
            rows = len(shape.table.rows)
            cols = len(shape.table.columns)
            if rows > 0:
                row_height = height / rows
                for row_index in range(1, rows):
                    y = top + int(row_height * row_index)
                    draw.line((left, y, left + width, y), fill="#cfe1f5", width=2)
            if cols > 0:
                col_width = width / cols
                for col_index in range(1, cols):
                    x = left + int(col_width * col_index)
                    draw.line((x, top, x, top + height), fill="#cfe1f5", width=2)
            header = shape.table.cell(0, 0).text.strip() if rows and cols else "表格"
            draw.text((left + 12, top + 10), header[:18] or "表格", fill="#214872", font=body_font)
            continue

        if getattr(shape, "has_text_frame", False):
            text = shape.text.strip()
            draw.rounded_rectangle(box, radius=18, fill="#ffffff", outline="#d5dfeb", width=2)
            lines = [line.strip() for line in text.splitlines() if line.strip()]
            if not lines:
                continue
            first_line = lines[0][:40]
            draw.text((left + 12, top + 10), first_line, fill="#102033", font=title_font)
            for line_index, line in enumerate(lines[1:4], start=1):
                draw.text((left + 12, top + 10 + line_index * 18), line[:42], fill="#4b627a", font=body_font)
            continue

        draw.rounded_rectangle(box, radius=18, fill="#eef5ff", outline="#d5dfeb", width=2)

    output = Path(output_path)
    output.parent.mkdir(parents=True, exist_ok=True)
    image.save(output)
    return SlidePreview(slide_number=slide_number, slide_count=slide_count, output_path=str(output))
