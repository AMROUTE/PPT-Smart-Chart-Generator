from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

try:
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
except ModuleNotFoundError:  # pragma: no cover
    plt = None

try:
    import pandas as pd
except ModuleNotFoundError:  # pragma: no cover
    pd = None

try:
    import seaborn as sns
except ModuleNotFoundError:  # pragma: no cover
    sns = None


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


def _ensure_dependencies() -> None:
    if pd is None:
        raise ModuleNotFoundError("pandas is required for chart generation.")
    if plt is None:
        raise ModuleNotFoundError("matplotlib is required for chart generation.")


def _ensure_dataframe(data: pd.DataFrame | list[dict[str, Any]] | dict[str, list[Any]]) -> pd.DataFrame:
    _ensure_dependencies()
    if isinstance(data, pd.DataFrame):
        dataframe = data.copy()
    else:
        dataframe = pd.DataFrame(data)

    if dataframe.empty:
        raise ValueError("Input data is empty. A chart cannot be generated from an empty DataFrame.")

    return dataframe


def _numeric_columns(dataframe: pd.DataFrame) -> list[str]:
    numeric = dataframe.select_dtypes(include="number").columns.tolist()
    if numeric:
        return numeric

    coerced_columns: list[str] = []
    for column in dataframe.columns:
        converted = pd.to_numeric(dataframe[column], errors="coerce")
        if converted.notna().any():
            dataframe[column] = converted
            coerced_columns.append(column)
    return coerced_columns


def _infer_x_column(dataframe: pd.DataFrame, numeric_columns: list[str]) -> str | None:
    non_numeric = [column for column in dataframe.columns if column not in numeric_columns]
    if non_numeric:
        return non_numeric[0]
    if dataframe.columns.tolist():
        return dataframe.columns[0]
    return None


def _infer_y_columns(
    dataframe: pd.DataFrame,
    numeric_columns: list[str],
    x_column: str | None,
    max_series: int | None = None,
) -> list[str]:
    y_columns = [column for column in numeric_columns if column != x_column]
    if not y_columns and x_column in numeric_columns:
        y_columns = [x_column]
    if max_series is not None:
        y_columns = y_columns[:max_series]
    return y_columns


def _prepare_output_path(output_path: str | Path | None, chart_type: str) -> Path:
    if output_path is None:
        output = Path("outputs") / f"{chart_type}_chart.png"
    else:
        output = Path(output_path)
    output.parent.mkdir(parents=True, exist_ok=True)
    return output


def _finalize_figure(output_path: Path) -> None:
    plt.tight_layout()
    plt.savefig(output_path, dpi=200, bbox_inches="tight")
    plt.close()


def _plot_bar(dataframe: pd.DataFrame, x_column: str, y_columns: list[str], title: str) -> None:
    plot_frame = dataframe.set_index(x_column)[y_columns]
    plot_frame.plot(kind="bar", figsize=(10, 6))
    plt.title(title)
    plt.xlabel(x_column)
    plt.ylabel("Value")
    plt.xticks(rotation=30, ha="right")


def _plot_line(dataframe: pd.DataFrame, x_column: str, y_columns: list[str], title: str) -> None:
    plot_frame = dataframe.set_index(x_column)[y_columns]
    plot_frame.plot(kind="line", marker="o", figsize=(10, 6))
    plt.title(title)
    plt.xlabel(x_column)
    plt.ylabel("Value")
    plt.xticks(rotation=30, ha="right")


def _plot_pie(dataframe: pd.DataFrame, x_column: str, y_columns: list[str], title: str) -> None:
    series = dataframe.groupby(x_column, dropna=False)[y_columns[0]].sum()
    plt.figure(figsize=(8, 8))
    plt.pie(series.values, labels=series.index.astype(str), autopct="%1.1f%%", startangle=90)
    plt.title(title)


def _plot_scatter(dataframe: pd.DataFrame, y_columns: list[str], title: str) -> None:
    if len(y_columns) < 2:
        raise ValueError("Scatter chart requires at least two numeric columns.")
    plt.figure(figsize=(10, 6))
    plt.scatter(dataframe[y_columns[0]], dataframe[y_columns[1]], s=60, alpha=0.75)
    plt.title(title)
    plt.xlabel(y_columns[0])
    plt.ylabel(y_columns[1])


def _plot_area(dataframe: pd.DataFrame, x_column: str, y_columns: list[str], title: str) -> None:
    plot_frame = dataframe.set_index(x_column)[y_columns]
    plot_frame.plot(kind="area", figsize=(10, 6), alpha=0.8)
    plt.title(title)
    plt.xlabel(x_column)
    plt.ylabel("Value")
    plt.xticks(rotation=30, ha="right")


def _plot_histogram(dataframe: pd.DataFrame, y_columns: list[str], title: str) -> None:
    plt.figure(figsize=(10, 6))
    dataframe[y_columns].plot(kind="hist", bins=12, alpha=0.6, figsize=(10, 6))
    plt.title(title)
    plt.xlabel("Value")
    plt.ylabel("Frequency")


def _plot_box(dataframe: pd.DataFrame, y_columns: list[str], title: str) -> None:
    plt.figure(figsize=(10, 6))
    dataframe[y_columns].plot(kind="box", figsize=(10, 6))
    plt.title(title)
    plt.ylabel("Value")


def _plot_heatmap(dataframe: pd.DataFrame, y_columns: list[str], title: str) -> None:
    plt.figure(figsize=(10, 6))
    matrix = dataframe[y_columns].corr()
    if sns is not None:
        sns.heatmap(matrix, annot=True, cmap="Blues", fmt=".2f")
    else:
        plt.imshow(matrix, cmap="Blues", aspect="auto")
        plt.colorbar()
        plt.xticks(range(len(matrix.columns)), matrix.columns, rotation=30, ha="right")
        plt.yticks(range(len(matrix.index)), matrix.index)
    plt.title(title)


def generate_chart(
    data: pd.DataFrame | list[dict[str, Any]] | dict[str, list[Any]],
    chart_type: str,
    output_path: str | Path | None = None,
    title: str | None = None,
    x_column: str | None = None,
    y_columns: list[str] | None = None,
) -> ChartGenerationResult:
    dataframe = _ensure_dataframe(data)
    normalized_chart_type = chart_type.lower().strip()
    if normalized_chart_type not in SUPPORTED_CHART_TYPES:
        raise ValueError(
            f"Unsupported chart type: {chart_type}. Supported types: {', '.join(SUPPORTED_CHART_TYPES)}."
        )

    numeric_columns = _numeric_columns(dataframe)
    inferred_x_column = x_column or _infer_x_column(dataframe, numeric_columns)
    inferred_y_columns = y_columns or _infer_y_columns(dataframe, numeric_columns, inferred_x_column)
    chart_title = title or f"{normalized_chart_type.title()} Chart"
    chart_output = _prepare_output_path(output_path, normalized_chart_type)

    if normalized_chart_type in {"bar", "line", "pie", "area"} and inferred_x_column is None:
        raise ValueError(f"{normalized_chart_type} chart requires at least one column for labels.")
    if normalized_chart_type != "heatmap" and not inferred_y_columns:
        raise ValueError("No numeric columns were found for chart generation.")
    if normalized_chart_type == "heatmap" and len(inferred_y_columns) < 2:
        raise ValueError("Heatmap requires at least two numeric columns.")

    plt.figure(figsize=(10, 6))

    if normalized_chart_type == "bar":
        _plot_bar(dataframe, inferred_x_column, inferred_y_columns, chart_title)
    elif normalized_chart_type == "line":
        _plot_line(dataframe, inferred_x_column, inferred_y_columns, chart_title)
    elif normalized_chart_type == "pie":
        _plot_pie(dataframe, inferred_x_column, inferred_y_columns, chart_title)
    elif normalized_chart_type == "scatter":
        _plot_scatter(dataframe, inferred_y_columns, chart_title)
    elif normalized_chart_type == "area":
        _plot_area(dataframe, inferred_x_column, inferred_y_columns, chart_title)
    elif normalized_chart_type == "histogram":
        _plot_histogram(dataframe, inferred_y_columns, chart_title)
    elif normalized_chart_type == "box":
        _plot_box(dataframe, inferred_y_columns, chart_title)
    elif normalized_chart_type == "heatmap":
        _plot_heatmap(dataframe, inferred_y_columns, chart_title)

    _finalize_figure(chart_output)
    return ChartGenerationResult(
        chart_type=normalized_chart_type,
        output_path=str(chart_output),
        x_column=inferred_x_column,
        y_columns=inferred_y_columns,
        title=chart_title,
    )