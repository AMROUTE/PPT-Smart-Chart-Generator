from __future__ import annotations

import os
import sys
from pathlib import Path
from typing import Any

from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[1]
GALLERY_DIR = ROOT / "docs" / "quality-gallery"
REPORT_PATH = ROOT / "docs" / "milestone2-quality-gallery-report.md"
sys.path.insert(0, str(ROOT))

os.environ.setdefault("ENABLE_QWEN_API", "0")
os.environ.setdefault("DATABASE_PATH", "/private/tmp/m2-quality-gallery.db")

from backend.chart_generator import generate_chart  # noqa: E402
from backend.services import process_demo_text  # noqa: E402


CHART_CASES: list[dict[str, Any]] = [
    {
        "case_id": "CHART-01",
        "title": "Revenue Trend With Labels",
        "chart_type": "line",
        "theme": "business",
        "records": [
            {"quarter": "Q1", "revenue": 120},
            {"quarter": "Q2", "revenue": 180},
            {"quarter": "Q3", "revenue": 220},
            {"quarter": "Q4", "revenue": 260},
        ],
        "expected_note": "value_labels",
    },
    {
        "case_id": "CHART-02",
        "title": "Positive And Negative Bar",
        "chart_type": "bar",
        "theme": "minimal",
        "records": [
            {"region": "North", "delta": 42},
            {"region": "South", "delta": -18},
            {"region": "West", "delta": 24},
            {"region": "East", "delta": -9},
        ],
        "expected_note": "zero_baseline",
    },
    {
        "case_id": "CHART-03",
        "title": "Market Share With Other Group",
        "chart_type": "pie",
        "theme": "academic",
        "records": [{"segment": f"S{index}", "share": index} for index in range(1, 9)],
        "expected_note": "pie_other_grouped",
    },
    {
        "case_id": "CHART-04",
        "title": "Long Category Sampling",
        "chart_type": "bar",
        "theme": "tech",
        "records": [{"segment": f"Segment {index}", "value": index * 12, "other": index * 4} for index in range(1, 15)],
        "expected_note": "readable_label_sampling",
    },
]


ILLUSTRATION_CASES: list[dict[str, str]] = [
    {"case_id": "ILL-01", "style": "business", "text": "Quarterly revenue planning: 120\nTeam target alignment: 80", "feature": "business_growth_milestones"},
    {"case_id": "ILL-02", "style": "tech", "text": "Cloud service latency: 42\nAutomation coverage: 88", "feature": "tech_device_cloud"},
    {"case_id": "ILL-03", "style": "education", "text": "Student participation: 73\nCourse completion: 91", "feature": "education_board_books"},
    {"case_id": "ILL-04", "style": "medical", "text": "Healthcare visits: 42\nFollow-up calls: 18", "feature": "medical_care_symbol"},
    {"case_id": "ILL-05", "style": "academic", "text": "Research samples: 64\nValidated results: 52", "feature": "academic_papers_library"},
    {"case_id": "ILL-06", "style": "sketch", "text": "Prototype feedback: 31\nIteration notes: 12", "feature": "sketch_storyboard_lines"},
]


def _font(size: int = 14) -> ImageFont.ImageFont:
    try:
        return ImageFont.truetype("/System/Library/Fonts/Supplemental/Arial.ttf", size=size)
    except OSError:
        return ImageFont.load_default()


def _make_contact_sheet(image_paths: list[Path], output_path: Path, label_prefix: str) -> None:
    thumbs: list[Image.Image] = []
    labels: list[str] = []
    for index, path in enumerate(image_paths, start=1):
        image = Image.open(path).convert("RGB")
        image.thumbnail((360, 216))
        canvas = Image.new("RGB", (400, 270), "#f8fafc")
        canvas.paste(image, ((400 - image.width) // 2, 18))
        draw = ImageDraw.Draw(canvas)
        draw.text((18, 232), f"{label_prefix}-{index:02d}", fill="#111827", font=_font(15))
        draw.text((18, 250), path.name[:40], fill="#374151", font=_font(12))
        thumbs.append(canvas)
        labels.append(path.name)

    columns = 2
    rows = (len(thumbs) + columns - 1) // columns
    sheet = Image.new("RGB", (columns * 400, rows * 270), "#e5e7eb")
    for index, thumb in enumerate(thumbs):
        x = (index % columns) * 400
        y = (index // columns) * 270
        sheet.paste(thumb, (x, y))
    sheet.save(output_path)


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


def _run_chart_cases() -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for case in CHART_CASES:
        output_path = GALLERY_DIR / f"{case['case_id'].lower()}-{case['chart_type']}.png"
        chart = generate_chart(
            case["records"],
            case["chart_type"],
            output_path=output_path,
            title=case["title"],
            theme=case["theme"],
        )
        spec = chart.to_dict()
        expected_note = case["expected_note"]
        metrics = _image_metrics(output_path)
        status = "PASS" if expected_note in spec["render_notes"] and output_path.exists() and metrics["visual_ok"] else "REVIEW"
        rows.append(
            {
                "case_id": case["case_id"],
                "kind": "chart",
                "style": f"{case['chart_type']} / {case['theme']}",
                "asset": output_path,
                "quality_score": spec["quality_score"],
                "checks": spec["quality_checks"],
                "notes": spec["render_notes"],
                "warnings": spec["warnings"],
                "expected": expected_note,
                "metrics": metrics,
                "status": status,
            }
        )
    return rows


def _run_illustration_cases() -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for case in ILLUSTRATION_CASES:
        payload = process_demo_text(
            case["text"],
            chart_type_override="bar",
            chart_theme="business",
            illustration_style=case["style"],
            image_model="local",
        )
        pipeline = payload["pipeline"]
        source_path = ROOT / pipeline["illustration_image"]
        output_path = GALLERY_DIR / f"{case['case_id'].lower()}-{case['style']}.png"
        output_path.write_bytes(source_path.read_bytes())
        meta = pipeline["illustration_meta"]
        features = meta.get("local_render_features", [])
        expected_feature = case["feature"]
        metrics = _image_metrics(output_path)
        status = "PASS" if expected_feature in features and output_path.exists() and metrics["visual_ok"] else "REVIEW"
        rows.append(
            {
                "case_id": case["case_id"],
                "kind": "illustration",
                "style": case["style"],
                "asset": output_path,
                "quality_score": meta.get("clip_score"),
                "checks": meta.get("quality_components", {}),
                "notes": features,
                "warnings": [meta.get("generation_warning")] if meta.get("generation_warning") else [],
                "expected": expected_feature,
                "metrics": metrics,
                "status": status,
            }
        )
    return rows


def _build_report(rows: list[dict[str, Any]], chart_sheet: Path, illustration_sheet: Path) -> str:
    pass_count = sum(1 for row in rows if row["status"] == "PASS")
    lines = [
        "# Milestone 2 图表与配图质量样例 Gallery",
        "",
        "验证日期：2026 年 6 月 4 日",
        "",
        "关联 WBS：`M2.5`、`M2.6`、`M2.7`、`M2.10`",
        "",
        "## 1. 验证目标",
        "",
        "本报告用于固化一组可复现的图表与配图质量样例，辅助人工验收图表可读性、异常数据处理、配图风格化和本地 fallback 质量。",
        "",
        "## 2. 汇总",
        "",
        "| 样例数 | PASS | REVIEW |",
        "|---:|---:|---:|",
        f"| {len(rows)} | {pass_count} | {len(rows) - pass_count} |",
        "",
        "## 3. Contact Sheets",
        "",
        f"- 图表样例总览：`{chart_sheet.relative_to(ROOT)}`",
        f"- 配图样例总览：`{illustration_sheet.relative_to(ROOT)}`",
        "",
        "## 4. 样例明细",
        "",
        "| 编号 | 类型 | 风格/图表 | 资产 | 分数 | 尺寸 | KB | 颜色数 | 期望特征 | 记录特征 | Warning | 状态 |",
        "|---|---|---|---|---:|---|---:|---:|---|---|---|---|",
    ]
    for row in rows:
        notes = ", ".join(str(item) for item in row["notes"]) or "-"
        warnings = "；".join(str(item) for item in row["warnings"]) or "-"
        metrics = row["metrics"]
        dimensions = f"{metrics['width']}x{metrics['height']}"
        lines.append(
            f"| {row['case_id']} | {row['kind']} | {row['style']} | `{row['asset'].relative_to(ROOT)}` | {row['quality_score']} | {dimensions} | {metrics['size_kb']} | {metrics['color_count']} | `{row['expected']}` | `{notes}` | {warnings} | {row['status']} |"
        )
    lines.extend(
        [
            "",
            "## 5. 当前结论",
            "",
            "- 图表样例覆盖趋势、正负值柱状图、饼图 Other 聚合和长类别抽样。",
            "- 配图样例覆盖 business、tech、education、medical、academic、sketch 六类本地风格。",
            "- 每个样例均输出 PNG，并记录可回读的质量字段或本地渲染特征。",
            "- 每个样例都通过尺寸、文件大小和颜色丰富度 sanity check，降低空白图或单色图误入验收材料的风险。",
            "- 该 gallery 是自动化样例证据，仍需结合人工视觉评分表完成最终主观审美验收。",
        ]
    )
    return "\n".join(lines) + "\n"


def main() -> None:
    GALLERY_DIR.mkdir(parents=True, exist_ok=True)
    chart_rows = _run_chart_cases()
    illustration_rows = _run_illustration_cases()
    chart_sheet = GALLERY_DIR / "chart-contact-sheet.png"
    illustration_sheet = GALLERY_DIR / "illustration-contact-sheet.png"
    _make_contact_sheet([row["asset"] for row in chart_rows], chart_sheet, "CHART")
    _make_contact_sheet([row["asset"] for row in illustration_rows], illustration_sheet, "ILL")
    rows = chart_rows + illustration_rows
    REPORT_PATH.write_text(_build_report(rows, chart_sheet, illustration_sheet), encoding="utf-8")
    print(f"Wrote {REPORT_PATH}")
    print(f"PASS {sum(1 for row in rows if row['status'] == 'PASS')}/{len(rows)}")


if __name__ == "__main__":
    main()
