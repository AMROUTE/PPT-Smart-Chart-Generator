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
SUPPORTED_CHART_THEMES = ("tech", "business", "minimal", "academic")

CANVAS_SIZE = (1200, 720)
PLOT_BOUNDS = (120, 160, 1040, 560)


@dataclass(frozen=True)
class ChartTheme:
    key: str
    display_name: str
    tagline: str
    background: str
    panel: str
    title: str
    subtitle: str
    axis: str
    grid: str
    frame: str
    series_colors: list[str]
    area_fills: list[str]
    heatmap_start: tuple[int, int, int]
    heatmap_end: tuple[int, int, int]


CHART_THEMES: dict[str, ChartTheme] = {
    "tech": ChartTheme(
        key="tech",
        display_name="Tech Theme",
        tagline="Technology Dashboard",
        background="#07111f",
        panel="#0d1b2a",
        title="#eef6ff",
        subtitle="#9dc8ff",
        axis="#d9ecff",
        grid="#214463",
        frame="#16304b",
        series_colors=["#45c7ff", "#4f8cff", "#2ee6a6", "#ffd166", "#ff7a90"],
        area_fills=["#123554", "#153f69", "#124e45"],
        heatmap_start=(21, 43, 67),
        heatmap_end=(69, 199, 255),
    ),
    "business": ChartTheme(
        key="business",
        display_name="Business Theme",
        tagline="Executive Summary",
        background="#f4f7fb",
        panel="#ffffff",
        title="#1f2937",
        subtitle="#64748b",
        axis="#334155",
        grid="#d9e2ec",
        frame="#c7d2de",
        series_colors=["#1d4ed8", "#0f766e", "#ca8a04", "#dc2626", "#7c3aed"],
        area_fills=["#bfdbfe", "#99f6e4", "#fde68a"],
        heatmap_start=(226, 232, 240),
        heatmap_end=(29, 78, 216),
    ),
    "minimal": ChartTheme(
        key="minimal",
        display_name="Minimal Theme",
        tagline="Clean Visual Summary",
        background="#fcfcfd",
        panel="#ffffff",
        title="#111827",
        subtitle="#6b7280",
        axis="#374151",
        grid="#e5e7eb",
        frame="#e5e7eb",
        series_colors=["#111827", "#4b5563", "#9ca3af", "#2563eb", "#10b981"],
        area_fills=["#e5e7eb", "#dbeafe", "#d1fae5"],
        heatmap_start=(243, 244, 246),
        heatmap_end=(17, 24, 39),
    ),
    "academic": ChartTheme(
        key="academic",
        display_name="Academic Theme",
        tagline="Research Presentation",
        background="#fffdf8",
        panel="#fffaf0",
        title="#3b2f2f",
        subtitle="#7c6f64",
        axis="#4b5563",
        grid="#e7dccb",
        frame="#d6c7b0",
        series_colors=["#8b5e3c", "#355c7d", "#6c8a3b", "#c06c84", "#f4a261"],
        area_fills=["#eadbc8", "#dbe7f0", "#e1ecd2"],
        heatmap_start=(246, 241, 231),
        heatmap_end=(53, 92, 125),
    ),
}
DEFAULT_CHART_THEME = "tech"


@dataclass
class ChartGenerationResult:
    chart_type: str
    output_path: str
    x_column: str | None
    y_columns: list[str]
    title: str
    theme: str
    fallback: bool = False
    warnings: list[str] | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "chart_type": self.chart_type,
            "output_path": self.output_path,
            "x_column": self.x_column,
            "y_columns": self.y_columns,
            "title": self.title,
            "theme": self.theme,
            "fallback": self.fallback,
            "warnings": self.warnings or [],
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

    return records


def _to_float(value: Any) -> float | None:
    try:
        number = float(value)
    except (TypeError, ValueError):
        return None
    if number != number or number in {float("inf"), float("-inf")}:
        return None
    return number


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
    labels = [str(record.get(x_column, f"Item {index + 1}")) for index, record in enumerate(records)] if x_column else [f"Item {index + 1}" for index in range(len(records))]
    series_values: list[list[float]] = []
    for column in y_columns:
        values = [_to_float(record.get(column)) or 0.0 for record in records]
        series_values.append(values)
    return labels, series_values


def _ensure_scatter_columns(records: list[dict[str, Any]], y_columns: list[str], warnings: list[str]) -> list[str]:
    if len(y_columns) >= 2:
        return y_columns[:2]
    for index, record in enumerate(records):
        record["_point_index"] = index + 1
    warnings.append("Scatter chart received fewer than two numeric columns; added synthetic point index.")
    if y_columns:
        return ["_point_index", y_columns[0]]
    return []


def _ensure_heatmap_columns(records: list[dict[str, Any]], y_columns: list[str], warnings: list[str]) -> list[str]:
    if len(y_columns) >= 2:
        return y_columns
    if y_columns:
        derived_column = f"{y_columns[0]}_baseline"
        for record in records:
            record[derived_column] = _to_float(record.get(y_columns[0])) or 0.0
        warnings.append("Heatmap received one numeric column; added a baseline column for stable rendering.")
        return [y_columns[0], derived_column]
    return []


def _sanitize_pie_values(values: list[float], warnings: list[str]) -> list[float]:
    sanitized = [max(0.0, value) for value in values]
    if sanitized != values:
        warnings.append("Pie chart converted negative values to zero.")
    if not any(value > 0 for value in sanitized):
        warnings.append("Pie chart received no positive values; using equal placeholder slices.")
        return [1.0 for _ in sanitized] or [1.0]
    return sanitized


def _resolve_theme(theme: str | None) -> ChartTheme:
    normalized = (theme or DEFAULT_CHART_THEME).strip().lower()
    return CHART_THEMES.get(normalized, CHART_THEMES[DEFAULT_CHART_THEME])


def _text_size(draw: ImageDraw.ImageDraw, text: str, font: ImageFont.ImageFont) -> tuple[int, int]:
    left, top, right, bottom = draw.textbbox((0, 0), text, font=font)
    return right - left, bottom - top


def _new_canvas(title: str, theme: ChartTheme) -> tuple[Image.Image, ImageDraw.ImageDraw, ImageFont.ImageFont, ImageFont.ImageFont]:
    image = Image.new("RGB", CANVAS_SIZE, theme.background)
    draw = ImageDraw.Draw(image)
    title_font = ImageFont.load_default()
    body_font = ImageFont.load_default()
    draw.rounded_rectangle((32, 32, CANVAS_SIZE[0] - 32, CANVAS_SIZE[1] - 32), radius=28, fill=theme.panel, outline=theme.frame, width=3)
    draw.rounded_rectangle((80, 110, 1080, 610), radius=24, outline=theme.frame, width=2)
    draw.text((120, 70), title, fill=theme.title, font=title_font)
    draw.text((120, 92), theme.tagline, fill=theme.subtitle, font=body_font)
    return image, draw, title_font, body_font


def _write_placeholder_chart(
    output_path: Path,
    chart_type: str,
    title: str,
    theme: ChartTheme,
    message: str,
    warnings: list[str],
) -> ChartGenerationResult:
    image, draw, title_font, body_font = _new_canvas(title, theme)
    left, top, right, bottom = PLOT_BOUNDS
    draw.rounded_rectangle((left, top, right, bottom), radius=24, fill=theme.background, outline=theme.frame, width=2)
    draw.text((left + 40, top + 64), "Fallback Chart Preview", fill=theme.title, font=title_font)
    draw.text((left + 40, top + 104), message, fill=theme.subtitle, font=body_font)
    draw.text((left + 40, top + 148), "The pipeline can continue; replace with richer data for a full chart.", fill=theme.subtitle, font=body_font)
    image.save(output_path)
    return ChartGenerationResult(
        chart_type=chart_type,
        output_path=str(output_path),
        x_column=None,
        y_columns=[],
        title=title,
        theme=theme.key,
        fallback=True,
        warnings=warnings,
    )


def _draw_axes(draw: ImageDraw.ImageDraw, theme: ChartTheme) -> None:
    left, top, right, bottom = PLOT_BOUNDS
    draw.line((left, top, left, bottom), fill=theme.axis, width=3)
    draw.line((left, bottom, right, bottom), fill=theme.axis, width=3)
    for index in range(1, 5):
        y = top + (bottom - top) * index / 5
        draw.line((left, y, right, y), fill=theme.grid, width=1)


def _label_x_axis(draw: ImageDraw.ImageDraw, labels: list[str], font: ImageFont.ImageFont, theme: ChartTheme) -> list[float]:
    left, _, right, bottom = PLOT_BOUNDS
    count = max(len(labels), 1)
    step = (right - left) / count
    centers: list[float] = []
    for index, label in enumerate(labels):
        center = left + step * (index + 0.5)
        centers.append(center)
        label_text = label[:10]
        width, _ = _text_size(draw, label_text, font)
        draw.text((center - width / 2, bottom + 16), label_text, fill=theme.axis, font=font)
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


def _draw_chart_legend(draw: ImageDraw.ImageDraw, labels: list[str], theme: ChartTheme, font: ImageFont.ImageFont) -> None:
    if not labels:
        return
    x = 840
    y = 118
    for index, label in enumerate(labels[:3]):
        color = theme.series_colors[index % len(theme.series_colors)]
        top = y + index * 24
        draw.rounded_rectangle((x, top, x + 12, top + 12), radius=3, fill=color)
        draw.text((x + 18, top - 1), label[:18], fill=theme.subtitle, font=font)


def _plot_bar(draw: ImageDraw.ImageDraw, labels: list[str], series_values: list[list[float]], y_columns: list[str], font: ImageFont.ImageFont, theme: ChartTheme) -> None:
    _draw_axes(draw, theme)
    centers = _label_x_axis(draw, labels, font, theme)
    _draw_chart_legend(draw, y_columns, theme, font)
    minimum, maximum = _value_scale(series_values)
    count = max(len(series_values[:3]), 1)
    bar_group_width = 92
    bar_width = max(14, int(bar_group_width / count) - 8)
    for series_index, values in enumerate(series_values[:3]):
        color = theme.series_colors[series_index]
        offset = (series_index - (count - 1) / 2) * (bar_width + 8)
        for point_index, value in enumerate(values):
            x = centers[point_index] + offset
            y = _value_to_y(value, minimum, maximum)
            draw.rounded_rectangle((x - bar_width / 2, y, x + bar_width / 2, PLOT_BOUNDS[3]), radius=8, fill=color)


def _plot_line(draw: ImageDraw.ImageDraw, labels: list[str], series_values: list[list[float]], y_columns: list[str], font: ImageFont.ImageFont, theme: ChartTheme, filled: bool = False) -> None:
    _draw_axes(draw, theme)
    centers = _label_x_axis(draw, labels, font, theme)
    _draw_chart_legend(draw, y_columns, theme, font)
    minimum, maximum = _value_scale(series_values)
    for series_index, values in enumerate(series_values[:3]):
        color = theme.series_colors[series_index]
        points = [(centers[index], _value_to_y(value, minimum, maximum)) for index, value in enumerate(values)]
        if filled and points:
            polygon = [(centers[0], PLOT_BOUNDS[3]), *points, (centers[-1], PLOT_BOUNDS[3])]
            draw.polygon(polygon, fill=theme.area_fills[series_index % len(theme.area_fills)])
        draw.line(points, fill=color, width=4)
        for x, y in points:
            draw.ellipse((x - 6, y - 6, x + 6, y + 6), fill=color, outline=theme.panel)


def _plot_pie(draw: ImageDraw.ImageDraw, labels: list[str], values: list[float], font: ImageFont.ImageFont, theme: ChartTheme) -> None:
    total = sum(values) or 1.0
    bbox = (180, 160, 620, 600)
    start = -90.0
    for index, value in enumerate(values):
        extent = 360.0 * value / total
        color = theme.series_colors[index % len(theme.series_colors)]
        draw.pieslice(bbox, start=start, end=start + extent, fill=color, outline=theme.panel)
        ratio = f"{(value / total) * 100:.1f}%"
        draw.text((700, 180 + index * 42), f"{labels[index][:10]} {ratio}", fill=theme.title, font=font)
        start += extent


def _plot_scatter(draw: ImageDraw.ImageDraw, x_values: list[float], y_values: list[float], font: ImageFont.ImageFont, theme: ChartTheme) -> None:
    _draw_axes(draw, theme)
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
        draw.ellipse((x - 9, y - 9, x + 9, y + 9), fill=theme.series_colors[0], outline=theme.title)
    draw.text((left, bottom + 16), "X", fill=theme.axis, font=font)
    draw.text((left - 24, top), "Y", fill=theme.axis, font=font)


def _plot_histogram(draw: ImageDraw.ImageDraw, values: list[float], font: ImageFont.ImageFont, theme: ChartTheme) -> None:
    _draw_axes(draw, theme)
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
        draw.rounded_rectangle((x0, y0, x0 + width - 20, bottom), radius=8, fill=theme.series_colors[1])
        draw.text((x0 + 8, bottom + 16), str(index + 1), fill=theme.axis, font=font)


def _plot_box(draw: ImageDraw.ImageDraw, series_values: list[list[float]], y_columns: list[str], font: ImageFont.ImageFont, theme: ChartTheme) -> None:
    _draw_axes(draw, theme)
    left, _, right, bottom = PLOT_BOUNDS
    minimum, maximum = _value_scale(series_values)
    step = (right - left) / max(len(series_values[:3]), 1)
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
        color = theme.series_colors[index]
        draw.line((center, _value_to_y(low, minimum, maximum), center, _value_to_y(high, minimum, maximum)), fill=color, width=4)
        draw.rectangle((box_left, _value_to_y(q3, minimum, maximum), box_right, _value_to_y(q1, minimum, maximum)), outline=color, width=4)
        draw.line((box_left, _value_to_y(median, minimum, maximum), box_right, _value_to_y(median, minimum, maximum)), fill=color, width=4)
        draw.text((center - 18, bottom + 16), y_columns[index][:8], fill=theme.axis, font=font)


def _blend_color(start: tuple[int, int, int], end: tuple[int, int, int], ratio: float) -> tuple[int, int, int]:
    return tuple(int(start[index] + (end[index] - start[index]) * ratio) for index in range(3))


def _plot_heatmap(draw: ImageDraw.ImageDraw, records: list[dict[str, Any]], y_columns: list[str], font: ImageFont.ImageFont, theme: ChartTheme) -> None:
    left, top, _, _ = PLOT_BOUNDS
    cell_w = 140
    cell_h = 84
    grid_values = [[_to_float(record.get(column)) or 0.0 for column in y_columns[:4]] for record in records[:4]]
    maximum = max((value for row in grid_values for value in row), default=1.0) or 1.0
    for row_index, row in enumerate(grid_values):
        for col_index, value in enumerate(row):
            ratio = 0.0 if maximum == 0 else value / maximum
            color = _blend_color(theme.heatmap_start, theme.heatmap_end, ratio)
            x0 = left + col_index * cell_w
            y0 = top + row_index * cell_h
            draw.rounded_rectangle((x0, y0, x0 + cell_w - 12, y0 + cell_h - 12), radius=12, fill=color, outline=theme.frame)
            draw.text((x0 + 36, y0 + 26), f"{value:g}", fill=theme.title, font=font)
    for col_index, column in enumerate(y_columns[:4]):
        draw.text((left + col_index * cell_w + 24, top - 28), column[:8], fill=theme.axis, font=font)


def generate_chart(
    data: list[dict[str, Any]] | dict[str, list[Any]],
    chart_type: str,
    output_path: str | Path | None = None,
    title: str | None = None,
    x_column: str | None = None,
    y_columns: list[str] | None = None,
    theme: str = DEFAULT_CHART_THEME,
) -> ChartGenerationResult:
    normalized_chart_type = chart_type.lower().strip()
    if normalized_chart_type not in SUPPORTED_CHART_TYPES:
        raise ValueError(f"Unsupported chart type: {chart_type}. Supported types: {', '.join(SUPPORTED_CHART_TYPES)}.")

    resolved_theme = _resolve_theme(theme)
    records = _coerce_records(data)
    chart_title = title or f"{normalized_chart_type.title()} Chart"
    chart_output = _prepare_output_path(output_path, normalized_chart_type)
    warnings: list[str] = []
    if not records:
        warnings.append("Input data is empty; rendered placeholder chart.")
        return _write_placeholder_chart(chart_output, normalized_chart_type, chart_title, resolved_theme, "No chartable data was provided.", warnings)

    numeric_columns = _numeric_columns(records)
    inferred_x_column = x_column or _infer_x_column(records, numeric_columns)
    inferred_y_columns = y_columns or _infer_y_columns(records, numeric_columns, inferred_x_column)
    if normalized_chart_type == "scatter":
        inferred_y_columns = _ensure_scatter_columns(records, inferred_y_columns, warnings)
    elif normalized_chart_type == "heatmap":
        inferred_y_columns = _ensure_heatmap_columns(records, inferred_y_columns, warnings)

    if normalized_chart_type in {"bar", "line", "pie", "area"} and inferred_x_column is None:
        warnings.append(f"{normalized_chart_type} chart has no label column; rendered placeholder chart.")
        return _write_placeholder_chart(chart_output, normalized_chart_type, chart_title, resolved_theme, "No label column was available.", warnings)
    if normalized_chart_type not in {"scatter", "heatmap"} and not inferred_y_columns:
        warnings.append("No numeric columns were found; rendered placeholder chart.")
        return _write_placeholder_chart(chart_output, normalized_chart_type, chart_title, resolved_theme, "No numeric values were available.", warnings)
    if normalized_chart_type in {"scatter", "heatmap"} and len(inferred_y_columns) < 2:
        warnings.append(f"{normalized_chart_type} chart needs at least two numeric columns; rendered placeholder chart.")
        return _write_placeholder_chart(chart_output, normalized_chart_type, chart_title, resolved_theme, "Not enough numeric values were available.", warnings)

    labels, series_values = _extract_series(records, inferred_x_column, inferred_y_columns)

    image, draw, _, body_font = _new_canvas(chart_title, resolved_theme)
    if normalized_chart_type == "bar":
        _plot_bar(draw, labels, series_values, inferred_y_columns, body_font, resolved_theme)
    elif normalized_chart_type == "line":
        _plot_line(draw, labels, series_values, inferred_y_columns, body_font, resolved_theme)
    elif normalized_chart_type == "pie":
        _plot_pie(draw, labels, _sanitize_pie_values(series_values[0], warnings), body_font, resolved_theme)
    elif normalized_chart_type == "scatter":
        _plot_scatter(draw, series_values[0], series_values[1], body_font, resolved_theme)
    elif normalized_chart_type == "area":
        _plot_line(draw, labels, series_values, inferred_y_columns, body_font, resolved_theme, filled=True)
    elif normalized_chart_type == "histogram":
        _plot_histogram(draw, series_values[0], body_font, resolved_theme)
    elif normalized_chart_type == "box":
        _plot_box(draw, series_values, inferred_y_columns, body_font, resolved_theme)
    elif normalized_chart_type == "heatmap":
        _plot_heatmap(draw, records, inferred_y_columns, body_font, resolved_theme)

    image.save(chart_output)
    return ChartGenerationResult(
        chart_type=normalized_chart_type,
        output_path=str(chart_output),
        x_column=inferred_x_column,
        y_columns=inferred_y_columns,
        title=chart_title,
        theme=resolved_theme.key,
        fallback=False,
        warnings=warnings,
    )
