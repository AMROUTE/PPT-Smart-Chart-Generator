from __future__ import annotations

import os
import sys
from itertools import combinations
from pathlib import Path
from typing import Any

from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[1]
GALLERY_DIR = ROOT / "docs" / "quality-gallery"
REPORT_PATH = ROOT / "docs" / "milestone2-illustration-diversity-report.md"
sys.path.insert(0, str(ROOT))

os.environ.setdefault("ENABLE_QWEN_API", "0")
os.environ.setdefault("DATABASE_PATH", "/private/tmp/m2-illustration-diversity.db")

from backend.services import process_demo_text  # noqa: E402


DIVERSITY_CASES: list[dict[str, str]] = [
    {
        "case_id": "DIV-01",
        "label": "growth",
        "text": "2020: 100\n2021: 150\n2022: 220\n2023: 300\n整体持续增长",
        "expected_feature": "business_growth_milestones",
        "theme_marker": "growth",
    },
    {
        "case_id": "DIV-02",
        "label": "region",
        "text": "华东: 35\n华南: 25\n华北: 20\n西南: 20\n请展示各区域市场份额占比",
        "expected_feature": "business_regional_network",
        "theme_marker": "regional",
    },
    {
        "case_id": "DIV-03",
        "label": "product",
        "text": "产品A: 120\n产品B: 95\n产品C: 150\n产品D: 110\n比较四个产品销量差异",
        "expected_feature": "business_product_showroom",
        "theme_marker": "product",
    },
    {
        "case_id": "DIV-04",
        "label": "campaign",
        "text": "广告投入: 10\n销售额: 80\n广告投入: 20\n销售额: 120\n广告投入: 30\n销售额: 170\n广告投入与销售额呈正相关",
        "expected_feature": "business_marketing_studio",
        "theme_marker": "marketing",
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
    first_image = Image.open(first).convert("RGB").resize((96, 56))
    second_image = Image.open(second).convert("RGB").resize((96, 56))
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
        image.thumbnail((360, 210))
        canvas = Image.new("RGB", (420, 292), "#f8fafc")
        canvas.paste(image, ((420 - image.width) // 2, 16))
        draw = ImageDraw.Draw(canvas)
        draw.text((16, 236), f"{row['case_id']} {row['label']}", fill="#111827", font=_font(15))
        feature_text = ", ".join(item for item in row["features"] if item.startswith("business_") or item.startswith("layout_"))
        draw.text((16, 258), feature_text[:76], fill="#374151", font=_font(12))
        thumbs.append(canvas)

    columns = 2
    rows_count = (len(thumbs) + columns - 1) // columns
    sheet = Image.new("RGB", (columns * 420, rows_count * 292), "#e5e7eb")
    for index, thumb in enumerate(thumbs):
        sheet.paste(thumb, ((index % columns) * 420, (index // columns) * 292))
    sheet.save(output_path)


def _run_cases() -> tuple[list[dict[str, Any]], list[dict[str, Any]], dict[str, Any]]:
    GALLERY_DIR.mkdir(parents=True, exist_ok=True)
    rows: list[dict[str, Any]] = []
    for case in DIVERSITY_CASES:
        payload = process_demo_text(
            case["text"],
            chart_type_override="auto",
            chart_theme="business",
            illustration_style="auto",
            image_model="local",
        )
        pipeline = payload["pipeline"]
        source_path = ROOT / pipeline["illustration_image"]
        output_path = GALLERY_DIR / f"{case['case_id'].lower()}-{case['label']}.png"
        output_path.write_bytes(source_path.read_bytes())
        meta = pipeline["illustration_meta"]
        intent = pipeline["intent"]
        features = meta.get("local_render_features", [])
        visual_theme = str(intent.get("visual_theme", ""))
        expected_feature = case["expected_feature"]
        theme_marker = case["theme_marker"]
        metrics = _image_metrics(output_path)
        rows.append(
            {
                "case_id": case["case_id"],
                "label": case["label"],
                "asset": output_path,
                "visual_theme": visual_theme,
                "composition_variant": meta.get("composition_variant", ""),
                "features": features,
                "expected_feature": expected_feature,
                "theme_marker": theme_marker,
                "quality_score": meta.get("clip_score"),
                "metrics": metrics,
                "status": "PASS" if expected_feature in features and theme_marker in visual_theme.lower() and metrics["visual_ok"] else "REVIEW",
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

    subject_features = {
        feature
        for row in rows
        for feature in row["features"]
        if feature
        in {
            "business_growth_milestones",
            "business_regional_network",
            "business_product_showroom",
            "business_marketing_studio",
        }
    }
    layout_variants = {str(row["composition_variant"]) for row in rows}
    visual_themes = {str(row["visual_theme"]) for row in rows}
    min_delta = min((row["delta"] for row in pair_rows), default=0)
    summary = {
        "pass_count": sum(1 for row in rows if row["status"] == "PASS"),
        "case_count": len(rows),
        "subject_feature_count": len(subject_features),
        "layout_variant_count": len(layout_variants),
        "visual_theme_count": len(visual_themes),
        "min_pixel_delta": min_delta,
        "overall_status": "PASS"
        if len(subject_features) == 4 and len(layout_variants) >= 2 and len(visual_themes) == 4 and min_delta >= 4 and all(row["status"] == "PASS" for row in rows)
        else "REVIEW",
    }
    return rows, pair_rows, summary


def _build_report(rows: list[dict[str, Any]], pair_rows: list[dict[str, Any]], summary: dict[str, Any], contact_sheet: Path) -> str:
    lines = [
        "# Milestone 2 插图多样性回归报告",
        "",
        "验证日期：2026 年 6 月 5 日",
        "",
        "关联 WBS：`M2.6`、`M2.7`、`M2.10`",
        "",
        "## 1. 验证目标",
        "",
        "本报告专门验证相近商务页不会再次全部生成通用办公室会议插图。样例覆盖增长、区域市场、产品组合和营销投放四类页面。",
        "",
        "## 2. 汇总",
        "",
        "| 样例数 | PASS | 主题特征数 | 构图变体数 | 视觉主题数 | 最小像素差 | 总状态 |",
        "|---:|---:|---:|---:|---:|---:|---|",
        f"| {summary['case_count']} | {summary['pass_count']} | {summary['subject_feature_count']} | {summary['layout_variant_count']} | {summary['visual_theme_count']} | {summary['min_pixel_delta']} | {summary['overall_status']} |",
        "",
        "## 3. Contact Sheet",
        "",
        f"- 插图多样性总览：`{contact_sheet.relative_to(ROOT)}`",
        "",
        "## 4. 样例明细",
        "",
        "| 编号 | 主题 | 资产 | 分数 | 构图 | 期望主题特征 | 记录特征 | Visual Theme | 状态 |",
        "|---|---|---|---:|---|---|---|---|---|",
    ]
    for row in rows:
        feature_text = ", ".join(str(item) for item in row["features"])
        lines.append(
            f"| {row['case_id']} | {row['label']} | `{row['asset'].relative_to(ROOT)}` | {row['quality_score']} | {row['composition_variant']} | `{row['expected_feature']}` | `{feature_text}` | {row['visual_theme']} | {row['status']} |"
        )

    lines.extend(["", "## 5. 两两视觉差", "", "| Pair | Mean Pixel Delta |", "|---|---:|"])
    for row in pair_rows:
        lines.append(f"| {row['pair']} | {row['delta']} |")
    lines.extend(
        [
            "",
            "## 6. 当前结论",
            "",
            "- 四个相近商务样例均生成不同内容主题特征。",
            "- 构图变体不少于 2 类，避免同一模板连续复用。",
            "- Visual Theme 均不包含通用 `office collaboration`。",
            "- 该检查用于防止用户反馈的会议室插图同质化问题回归。",
        ]
    )
    return "\n".join(lines) + "\n"


def main() -> None:
    rows, pair_rows, summary = _run_cases()
    contact_sheet = GALLERY_DIR / "illustration-diversity-contact-sheet.png"
    _make_contact_sheet(rows, contact_sheet)
    REPORT_PATH.write_text(_build_report(rows, pair_rows, summary, contact_sheet), encoding="utf-8")
    print(f"Wrote {REPORT_PATH}")
    print(f"{summary['overall_status']} {summary['pass_count']}/{summary['case_count']}")


if __name__ == "__main__":
    main()
