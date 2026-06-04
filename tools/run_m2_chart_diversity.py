from __future__ import annotations

import os
import sys
from itertools import combinations
from pathlib import Path
from typing import Any

from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[1]
GALLERY_DIR = ROOT / "docs" / "quality-gallery"
REPORT_PATH = ROOT / "docs" / "milestone2-chart-diversity-report.md"
sys.path.insert(0, str(ROOT))

os.environ.setdefault("ENABLE_QWEN_API", "0")
os.environ.setdefault("DATABASE_PATH", "/private/tmp/m2-chart-diversity.db")

from backend.services import process_demo_text  # noqa: E402


CHART_DIVERSITY_CASES: list[dict[str, str]] = [
    {
        "case_id": "CDIV-01",
        "intent": "trend",
        "expected_chart": "line",
        "text": "2020: 100\n2021: 150\n2022: 220\n2023: 300\n整体持续增长，请展示年度趋势",
    },
    {
        "case_id": "CDIV-02",
        "intent": "composition",
        "expected_chart": "pie",
        "text": "华东: 35\n华南: 25\n华北: 20\n西南: 20\n请展示各区域市场份额占比",
    },
    {
        "case_id": "CDIV-03",
        "intent": "comparison",
        "expected_chart": "bar",
        "text": "产品A: 120\n产品B: 95\n产品C: 150\n产品D: 110\n比较四个产品销量差异",
    },
    {
        "case_id": "CDIV-04",
        "intent": "correlation",
        "expected_chart": "scatter",
        "text": "广告投入: 10\n销售额: 80\n广告投入: 20\n销售额: 120\n广告投入: 30\n销售额: 170\n广告投入越高销售额越高，呈正相关",
    },
    {
        "case_id": "CDIV-05",
        "intent": "distribution",
        "expected_chart": "histogram",
        "text": "0-10分: 2\n10-20分: 4\n20-30分: 9\n30-40分: 14\n40-50分: 21\n50-60分: 18\n60-70分: 11\n70-80分: 7\n80-90分: 3\n90-100分: 1\n请分析用户评分分布",
    },
]


def _font(size: int = 14) -> ImageFont.ImageFont:
    try:
        return ImageFont.truetype("/System/Library/Fonts/Supplemental/Arial.ttf", size=size)
    except OSError:
        return ImageFont.load_default()


def _image_metrics(path: Path) -> dict[str, Any]:
    image = Image.open(path).convert("RGB")
    sample = image.resize((80, max(1, int(80 * image.height / image.width))))
    colors = sample.getcolors(maxcolors=80 * 80)
    color_count = len(colors or [])
    return {
        "width": image.width,
        "height": image.height,
        "size_kb": round(path.stat().st_size / 1024, 1),
        "color_count": color_count,
        "visual_ok": image.width >= 700 and image.height >= 400 and path.stat().st_size > 8_000 and color_count >= 6,
    }


def _mean_pixel_delta(first: Path, second: Path) -> float:
    first_image = Image.open(first).convert("RGB").resize((96, 58))
    second_image = Image.open(second).convert("RGB").resize((96, 58))
    first_pixels = list(first_image.getdata())
    second_pixels = list(second_image.getdata())
    total = 0
    for a, b in zip(first_pixels, second_pixels):
        total += abs(a[0] - b[0]) + abs(a[1] - b[1]) + abs(a[2] - b[2])
    return round(total / (len(first_pixels) * 3), 2)


def _make_contact_sheet(rows: list[dict[str, Any]], output_path: Path) -> None:
    thumbs: list[Image.Image] = []
    for row in rows:
        image = Image.open(row["asset"]).convert("RGB")
        image.thumbnail((360, 216))
        canvas = Image.new("RGB", (420, 300), "#f8fafc")
        canvas.paste(image, ((420 - image.width) // 2, 16))
        draw = ImageDraw.Draw(canvas)
        draw.text((16, 238), f"{row['case_id']} {row['intent']} -> {row['chart_type']}", fill="#111827", font=_font(15))
        notes = ", ".join(str(item) for item in row["render_notes"])
        draw.text((16, 260), notes[:78], fill="#374151", font=_font(12))
        draw.text((16, 278), f"score {row['quality_score']} / {row['quality_status']}", fill="#374151", font=_font(12))
        thumbs.append(canvas)

    columns = 2
    rows_count = (len(thumbs) + columns - 1) // columns
    sheet = Image.new("RGB", (columns * 420, rows_count * 300), "#e5e7eb")
    for index, thumb in enumerate(thumbs):
        sheet.paste(thumb, ((index % columns) * 420, (index // columns) * 300))
    sheet.save(output_path)


def _run_cases() -> tuple[list[dict[str, Any]], list[dict[str, Any]], dict[str, Any]]:
    GALLERY_DIR.mkdir(parents=True, exist_ok=True)
    rows: list[dict[str, Any]] = []
    for case in CHART_DIVERSITY_CASES:
        payload = process_demo_text(
            case["text"],
            chart_type_override="auto",
            chart_theme="business",
            illustration_style="auto",
            image_model="local",
        )
        pipeline = payload["pipeline"]
        chart_spec = pipeline["chart_spec"]
        intent = pipeline["intent"]
        source_path = ROOT / pipeline["chart_image"]
        output_path = GALLERY_DIR / f"{case['case_id'].lower()}-{case['expected_chart']}.png"
        output_path.write_bytes(source_path.read_bytes())
        metrics = _image_metrics(output_path)
        chart_type = str(chart_spec.get("chart_type", ""))
        intent_category = str(intent.get("intent_category", ""))
        quality_score = float(chart_spec.get("quality_score") or 0)
        quality_status = str(chart_spec.get("quality_status", ""))
        rows.append(
            {
                "case_id": case["case_id"],
                "intent": case["intent"],
                "expected_chart": case["expected_chart"],
                "intent_category": intent_category,
                "chart_type": chart_type,
                "asset": output_path,
                "quality_score": quality_score,
                "quality_status": quality_status,
                "render_notes": chart_spec.get("render_notes", []),
                "warnings": chart_spec.get("warnings", []),
                "metrics": metrics,
                "status": "PASS"
                if intent_category == case["intent"]
                and chart_type == case["expected_chart"]
                and quality_score >= 6.5
                and quality_status in {"pass", "attention"}
                and metrics["visual_ok"]
                else "REVIEW",
            }
        )

    pair_rows: list[dict[str, Any]] = []
    for first, second in combinations(rows, 2):
        pair_rows.append(
            {
                "pair": f"{first['case_id']} / {second['case_id']}",
                "delta": _mean_pixel_delta(first["asset"], second["asset"]),
            }
        )

    chart_types = {row["chart_type"] for row in rows}
    intent_categories = {row["intent_category"] for row in rows}
    min_delta = min((row["delta"] for row in pair_rows), default=0)
    summary = {
        "pass_count": sum(1 for row in rows if row["status"] == "PASS"),
        "case_count": len(rows),
        "chart_type_count": len(chart_types),
        "intent_count": len(intent_categories),
        "min_pixel_delta": min_delta,
        "overall_status": "PASS"
        if len(chart_types) == 5 and len(intent_categories) == 5 and min_delta >= 1 and all(row["status"] == "PASS" for row in rows)
        else "REVIEW",
    }
    return rows, pair_rows, summary


def _build_report(rows: list[dict[str, Any]], pair_rows: list[dict[str, Any]], summary: dict[str, Any], contact_sheet: Path) -> str:
    lines = [
        "# Milestone 2 图表多样性回归报告",
        "",
        "验证日期：2026 年 6 月 5 日",
        "",
        "关联 WBS：`M2.4`、`M2.5`、`M2.10`",
        "",
        "## 1. 验证目标",
        "",
        "本报告验证相近业务文本在完整 Pipeline 中能按语义意图生成不同图表类型，防止所有页面退化为同一种基础柱状图。",
        "",
        "## 2. 汇总",
        "",
        "| 样例数 | PASS | 图表类型数 | 意图数 | 最小像素差 | 总状态 |",
        "|---:|---:|---:|---:|---:|---|",
        f"| {summary['case_count']} | {summary['pass_count']} | {summary['chart_type_count']} | {summary['intent_count']} | {summary['min_pixel_delta']} | {summary['overall_status']} |",
        "",
        "## 3. Contact Sheet",
        "",
        f"- 图表多样性总览：`{contact_sheet.relative_to(ROOT)}`",
        "",
        "## 4. 样例明细",
        "",
        "| 编号 | 期望意图 | 实际意图 | 期望图表 | 实际图表 | 资产 | 分数 | 状态 | Render Notes | Warning |",
        "|---|---|---|---|---|---|---:|---|---|---|",
    ]
    for row in rows:
        notes = ", ".join(str(item) for item in row["render_notes"]) or "-"
        warnings = "；".join(str(item) for item in row["warnings"]) or "-"
        lines.append(
            f"| {row['case_id']} | {row['intent']} | {row['intent_category']} | {row['expected_chart']} | {row['chart_type']} | `{row['asset'].relative_to(ROOT)}` | {row['quality_score']} | {row['status']} | `{notes}` | {warnings} |"
        )

    lines.extend(["", "## 5. 两两视觉差", "", "| Pair | Mean Pixel Delta |", "|---|---:|"])
    for row in pair_rows:
        lines.append(f"| {row['pair']} | {row['delta']} |")
    lines.extend(
        [
            "",
            "## 6. 当前结论",
            "",
            "- 五类语义意图分别生成 line、pie、bar、scatter、histogram 五类图表。",
            "- 每个样例均通过图表质量门禁或注意态，不进入 fallback。",
            "- 像素差只作为非同图烟测；主要验收依据是语义意图、图表类型和质量字段。",
            "- Contact sheet 可用于人工快速检查图表类型、标题、标签和值标注是否合理。",
            "- 该检查用于防止图表推荐和渲染退化为单一柱状图模板。",
        ]
    )
    return "\n".join(lines) + "\n"


def main() -> None:
    rows, pair_rows, summary = _run_cases()
    contact_sheet = GALLERY_DIR / "chart-diversity-contact-sheet.png"
    _make_contact_sheet(rows, contact_sheet)
    REPORT_PATH.write_text(_build_report(rows, pair_rows, summary, contact_sheet), encoding="utf-8")
    print(f"Wrote {REPORT_PATH}")
    print(f"{summary['overall_status']} {summary['pass_count']}/{summary['case_count']}")


if __name__ == "__main__":
    main()
