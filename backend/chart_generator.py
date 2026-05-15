from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

from PIL import Image, ImageDraw, ImageFont


SUPPORTED_CHART_TYPES = (
    "bar",
    "line",
    "pie",
    "scatter",
    "area",
    "histogram",
    "box",
    "heatmap",
)

CANVAS_SIZE = (1200, 720)
PLOT_BOUNDS = (120, 140, 1040, 560)
BACKGROUND = "#ffffff"
TEXT = "#102033"
GRID = "#d8e5f2"
SERIES_COLORS = ["#2563eb", "#0ea5e9", "#22c55e", "#f59e0b", "#ef4444"]


@dataclass
class ChartGenerationResult:
    chart_type: str
    output_path: str
    x_column: str | None
    y_columns: list[str]
    title: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "chart_type": self.chart_type,
            "output_path": self.output_path,
            "x_column": self.x_column,
            "y_columns": self.y_columns,
            "title": self.title,
        }


def _prepare_output_path(output_path: str | Path | None, chart_type: str) -> Path:
    output = Path(output_path) if output_path is not None else Path("outputs") / f"{chart_type}_chart.png"
    output.parent.mkdir(parents=True, exist_ok=True)
    return output


def _coerce_records(data: Any) -> list[dict[str, Any]]:
    if isinstance(data, list):
        records = [dict(item) for item in data if isinstance(item, dict)]
    elif isinstance(data, dict):
        keys = list(data.keys())
        length = max((len(values) for values in data.values() if isinstance(values, list)), default=0)
        records = []
        for index in range(length):
            row: dict[str, Any] = {}
            for key in keys:
                values = data.get(key, [])
                row[key] = values[index] if isinstance(values, list) and index < len(values) else None
            records.append(row)
    else:
        raise ValueError("Unsupported data format for chart generation.")

    if not records:
        raise ValueError("Input data is empty. A chart cannot be generated from an empty dataset.")
    return records


def _to_float(value: Any) -> float | None:
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _numeric_columns(records: list[dict[str, Any]]) -> list[str]:
    columns = list(records[0].keys())
    numeric: list[str] = []
    for column in columns:
        values = [_to_float(record.get(column)) for record in records]
        if any(value is not None for value in values):
            numeric.append(column)
    return numeric


def _infer_x_column(records: list[dict[str, Any]], numeric_columns: list[str]) -> str | None:
    for column in records[0].keys():
        if column not in numeric_columns:
            return column
    return next(iter(records[0].keys()), None)


def _infer_y_columns(
    records: list[dict[str, Any]],
    numeric_columns: list[str],
    x_column: str | None,
    max_series: int | None = None,
) -> list[str]:
    y_columns = [column for column in numeric_columns if column != x_column]
    if not y_columns and x_column in numeric_columns:
        y_columns = [x_column]
    return y_columns[:max_series] if max_series is not None else y_columns


def _extract_series(records: list[dict[str, Any]], x_column: str | None, y_columns: list[str]) -> tuple[list[str], list[list[float]]]:
    labels = [str(record.get(x_column, f"Item {index + 1}")) for index, record in enumerate(records)] if x_column else [
        f"Item {index + 1}" for index in range(len(records))
    ]
    series_values: list[list[float]] = []
    for column in y_columns:
        values = [_to_float(record.get(column)) or 0.0 for record in records]
        series_values.append(values)
    return labels, series_values


def _new_canvas(title: str) -> tuple[Image.Image, ImageDraw.ImageDraw, ImageFont.ImageFont, ImageFont.ImageFont]:
    image = Image.new("RGB", CANVAS_SIZE, BACKGROUND)
    draw = ImageDraw.Draw(image)
    title_font = ImageFont.load_default()
    body_font = ImageFont.load_default()
    draw.text((120, 70), title, fill=TEXT, font=title_font)
    return image, draw, title_font, body_font


def _draw_axes(draw: ImageDraw.ImageDraw) -> None:
    left, top, right, bottom = PLOT_BOUNDS
    draw.line((left, top, left, bottom), fill=TEXT, width=3)
    draw.line((left, bottom, right, bottom), fill=TEXT, width=3)
    for index in range(1, 5):
        y = top + (bottom - top) * index / 5
        draw.line((left, y, right, y), fill=GRID, width=1)


def _label_x_axis(draw: ImageDraw.ImageDraw, labels: list[str], font: ImageFont.ImageFont) -> list[float]:
    left, _, right, bottom = PLOT_BOUNDS
    count = max(len(labels), 1)
    step = (right - left) / count
    centers: list[float] = []
    for index, label in enumerate(labels):
        center = left + step * (index + 0.5)
        centers.append(center)
        draw.text((center - 18, bottom + 16), label[:8], fill=TEXT, font=font)
    return centers


def _value_scale(series_values: list[list[float]]) -> tuple[float, float]:
    flat = [value for series in series_values for value in series]
    minimum = min(flat) if flat else 0.0
    maximum = max(flat) if flat else 1.0
    if minimum == maximum:
        maximum = minimum + 1.0
    return minimum, maximum


def _value_to_y(value: float, minimum: float, maximum: float) -> float:
    _, top, _, bottom = PLOT_BOUNDS
    span = maximum - minimum or 1.0
    normalized = (value - minimum) / span
    return bottom - normalized * (bottom - top - 20)


def _plot_bar(draw: ImageDraw.ImageDraw, labels: list[str], series_values: list[list[float]], font: ImageFont.ImageFont) -> None:
    _draw_axes(draw)
    centers = _label_x_axis(draw, labels, font)
    minimum, maximum = _value_scale(series_values)
    count = max(len(series_values), 1)
    bar_group_width = 90
    bar_width = max(14, int(bar_group_width / count) - 8)
    for series_index, values in enumerate(series_values[:3]):
        color = SERIES_COLORS[series_index]
        offset = (series_index - (count - 1) / 2) * (bar_width + 8)
        for point_index, value in enumerate(values):
            x = centers[point_index] + offset
            y = _value_to_y(value, minimum, maximum)
            draw.rounded_rectangle((x - bar_width / 2, y, x + bar_width / 2, PLOT_BOUNDS[3]), radius=8, fill=color)


def _plot_line(draw: ImageDraw.ImageDraw, labels: list[str], series_values: list[list[float]], font: ImageFont.ImageFont, filled: bool = False) -> None:
    _draw_axes(draw)
    centers = _label_x_axis(draw, labels, font)
    minimum, maximum = _value_scale(series_values)
    for series_index, values in enumerate(series_values[:3]):
        color = SERIES_COLORS[series_index]
        points = [(centers[index], _value_to_y(value, minimum, maximum)) for index, value in enumerate(values)]
        if filled:
            polygon = [(centers[0], PLOT_BOUNDS[3]), *points, (centers[-1], PLOT_BOUNDS[3])]
            fill_color = "#bfdbfe" if series_index == 0 else "#bae6fd"
            draw.polygon(polygon, fill=fill_color)
        draw.line(points, fill=color, width=5)
        for x, y in points:
            draw.ellipse((x - 6, y - 6, x + 6, y + 6), fill=color)


def _plot_pie(draw: ImageDraw.ImageDraw, labels: list[str], values: list[float], font: ImageFont.ImageFont) -> None:
    total = sum(values) or 1.0
    bbox = (180, 160, 620, 600)
    start = -90.0
    for index, value in enumerate(values):
        extent = 360.0 * value / total
        color = SERIES_COLORS[index % len(SERIES_COLORS)]
        draw.pieslice(bbox, start=start, end=start + extent, fill=color)
        draw.text((700, 180 + index * 42), f"{labels[index][:10]} {value:g}", fill=color, font=font)
        start += extent


def _plot_scatter(draw: ImageDraw.ImageDraw, x_values: list[float], y_values: list[float], font: ImageFont.ImageFont) -> None:
    _draw_axes(draw)
    x_min, x_max = min(x_values), max(x_values)
    y_min, y_max = min(y_values), max(y_values)
    if x_min == x_max:
        x_max = x_min + 1.0
    if y_min == y_max:
        y_max = y_min + 1.0
    left, top, right, bottom = PLOT_BOUNDS
    for x_value, y_value in zip(x_values, y_values):
        x = left + (x_value - x_min) / (x_max - x_min) * (right - left - 20) + 10
        y = _value_to_y(y_value, y_min, y_max)
        draw.ellipse((x - 9, y - 9, x + 9, y + 9), fill=SERIES_COLORS[0])
    draw.text((left, bottom + 16), "X", fill=TEXT, font=font)
    draw.text((left - 26, top), "Y", fill=TEXT, font=font)


def _plot_histogram(draw: ImageDraw.ImageDraw, values: list[float], font: ImageFont.ImageFont) -> None:
    _draw_axes(draw)
    left, _, right, bottom = PLOT_BOUNDS
    bins = min(8, max(4, len(values)))
    minimum = min(values)
    maximum = max(values)
    if minimum == maximum:
        maximum = minimum + 1.0
    counts = [0] * bins
    for value in values:
        index = min(int((value - minimum) / (maximum - minimum) * bins), bins - 1)
        counts[index] += 1
    max_count = max(counts) or 1
    width = (right - left) / bins
    for index, count in enumerate(counts):
        bar_height = count / max_count * (bottom - PLOT_BOUNDS[1] - 20)
        x0 = left + index * width + 10
        y0 = bottom - bar_height
        draw.rounded_rectangle((x0, y0, x0 + width - 20, bottom), radius=8, fill=SERIES_COLORS[1])
        draw.text((x0 + 8, bottom + 16), str(index + 1), fill=TEXT, font=font)


def _plot_box(draw: ImageDraw.ImageDraw, series_values: list[list[float]], y_columns: list[str], font: ImageFont.ImageFont) -> None:
    _draw_axes(draw)
    left, top, right, bottom = PLOT_BOUNDS
    minimum, maximum = _value_scale(series_values)
    step = (right - left) / max(len(series_values), 1)
    for index, values in enumerate(series_values[:3]):
        sorted_values = sorted(values)
        q1 = sorted_values[len(sorted_values) // 4]
        median = sorted_values[len(sorted_values) // 2]
        q3 = sorted_values[(len(sorted_values) * 3) // 4]
        low = sorted_values[0]
        high = sorted_values[-1]
        center = left + step * (index + 0.5)
        box_left = center - 34
        box_right = center + 34
        draw.line((center, _value_to_y(low, minimum, maximum), center, _value_to_y(high, minimum, maximum)), fill=SERIES_COLORS[index], width=4)
        draw.rectangle((box_left, _value_to_y(q3, minimum, maximum), box_right, _value_to_y(q1, minimum, maximum)), outline=SERIES_COLORS[index], width=4)
        draw.line((box_left, _value_to_y(median, minimum, maximum), box_right, _value_to_y(median, minimum, maximum)), fill=SERIES_COLORS[index], width=4)
        draw.text((center - 18, bottom + 16), y_columns[index][:8], fill=TEXT, font=font)


def _plot_heatmap(draw: ImageDraw.ImageDraw, records: list[dict[str, Any]], y_columns: list[str], font: ImageFont.ImageFont) -> None:
    left, top, _, _ = PLOT_BOUNDS
    cell_w = 140
    cell_h = 84
    grid_values = [[_to_float(record.get(column)) or 0.0 for column in y_columns[:4]] for record in records[:4]]
    maximum = max((value for row in grid_values for value in row), default=1.0) or 1.0
    for row_index, row in enumerate(grid_values):
        for col_index, value in enumerate(row):
            intensity = int(230 - (value / maximum) * 150)
            color = (80, 140, intensity)
            x0 = left + col_index * cell_w
            y0 = top + row_index * cell_h
            draw.rounded_rectangle((x0, y0, x0 + cell_w - 12, y0 + cell_h - 12), radius=12, fill=color)
            draw.text((x0 + 36, y0 + 26), f"{value:g}", fill="#ffffff", font=font)
    for col_index, column in enumerate(y_columns[:4]):
        draw.text((left + col_index * cell_w + 24, top - 28), column[:8], fill=TEXT, font=font)


def generate_chart(
    data: list[dict[str, Any]] | dict[str, list[Any]],
    chart_type: str,
    output_path: str | Path | None = None,
    title: str | None = None,
    x_column: str | None = None,
    y_columns: list[str] | None = None,
) -> ChartGenerationResult:
    normalized_chart_type = chart_type.lower().strip()
    if normalized_chart_type not in SUPPORTED_CHART_TYPES:
        raise ValueError(f"Unsupported chart type: {chart_type}. Supported types: {', '.join(SUPPORTED_CHART_TYPES)}.")

    records = _coerce_records(data)
    numeric_columns = _numeric_columns(records)
    inferred_x_column = x_column or _infer_x_column(records, numeric_columns)
    inferred_y_columns = y_columns or _infer_y_columns(records, numeric_columns, inferred_x_column)
    if normalized_chart_type in {"bar", "line", "pie", "area"} and inferred_x_column is None:
        raise ValueError(f"{normalized_chart_type} chart requires at least one column for labels.")
    if normalized_chart_type == "scatter" and len(inferred_y_columns) < 2:
        raise ValueError("Scatter chart requires at least two numeric columns.")
    if normalized_chart_type == "heatmap" and len(inferred_y_columns) < 2:
        raise ValueError("Heatmap requires at least two numeric columns.")
    if normalized_chart_type not in {"scatter", "heatmap"} and not inferred_y_columns:
        raise ValueError("No numeric columns were found for chart generation.")

    chart_title = title or f"{normalized_chart_type.title()} Chart"
    chart_output = _prepare_output_path(output_path, normalized_chart_type)
    labels, series_values = _extract_series(records, inferred_x_column, inferred_y_columns)

    image, draw, _, body_font = _new_canvas(chart_title)
    if normalized_chart_type == "bar":
        _plot_bar(draw, labels, series_values, body_font)
    elif normalized_chart_type == "line":
        _plot_line(draw, labels, series_values, body_font)
    elif normalized_chart_type == "pie":
        _plot_pie(draw, labels, series_values[0], body_font)
    elif normalized_chart_type == "scatter":
        _plot_scatter(draw, series_values[0], series_values[1], body_font)
    elif normalized_chart_type == "area":
        _plot_line(draw, labels, series_values, body_font, filled=True)
    elif normalized_chart_type == "histogram":
        _plot_histogram(draw, series_values[0], body_font)
    elif normalized_chart_type == "box":
        _plot_box(draw, series_values, inferred_y_columns, body_font)
    elif normalized_chart_type == "heatmap":
        _plot_heatmap(draw, records, inferred_y_columns, body_font)

    image.save(chart_output)
    return ChartGenerationResult(
        chart_type=normalized_chart_type,
        output_path=str(chart_output),
        x_column=inferred_x_column,
        y_columns=inferred_y_columns,
        title=chart_title,
    )
