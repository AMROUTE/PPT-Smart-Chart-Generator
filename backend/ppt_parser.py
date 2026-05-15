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


def _normalized_cell_text(cell: Any) -> str:
    text = cell.text.strip()
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    if lines:
        return lines[0]
    return text


def _cell_merge_meta(cell: Any, row_index: int, col_index: int) -> dict[str, Any]:
    return {
        "row": row_index,
        "col": col_index,
        "text": _normalized_cell_text(cell),
        "is_merge_origin": bool(getattr(cell, "is_merge_origin", False)),
        "is_spanned": bool(getattr(cell, "is_spanned", False)),
        "row_span": int(getattr(cell, "span_height", 1) or 1),
        "col_span": int(getattr(cell, "span_width", 1) or 1),
    }


def extract_table_matrix(table: Any) -> list[list[dict[str, Any]]]:
    matrix: list[list[dict[str, Any]]] = []
    for row_index, row in enumerate(table.rows):
        matrix.append(
            [
                _cell_merge_meta(cell, row_index, col_index)
                for col_index, cell in enumerate(row.cells)
            ]
        )
    return matrix


def _resolve_visible_value(matrix: list[list[dict[str, Any]]], row_index: int, col_index: int) -> str:
    cell = matrix[row_index][col_index]
    if not cell["is_spanned"]:
        return cell["text"]

    for source_row in range(row_index, -1, -1):
        for source_col in range(col_index, -1, -1):
            source = matrix[source_row][source_col]
            if not source["is_merge_origin"]:
                continue

            row_end = source_row + source["row_span"] - 1
            col_end = source_col + source["col_span"] - 1
            if source_row <= row_index <= row_end and source_col <= col_index <= col_end:
                return source["text"]
    return cell["text"]


def table_to_dataframe(table: Any) -> pd.DataFrame:
    if pd is None:
        raise ModuleNotFoundError("pandas is required for table_to_dataframe.")

    raw_matrix = extract_table_matrix(table)
    matrix = [
        [_resolve_visible_value(raw_matrix, row_index, col_index) for col_index in range(len(row))]
        for row_index, row in enumerate(raw_matrix)
    ]
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
    return shape.text.strip()


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

        table_matrix = extract_table_matrix(shape.table)
        dataframe = table_to_dataframe(shape.table)
        tables.append(
            {
                "title": getattr(shape, "name", f"table_{table_index}"),
                "columns": dataframe.columns.tolist(),
                "rows": dataframe_to_records(dataframe),
                "dataframe": dataframe,
                "cell_matrix": table_matrix,
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