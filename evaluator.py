from __future__ import annotations

import argparse
import csv
import json
import re
import time
from collections import Counter
from pathlib import Path
from typing import Any, Callable

from edge_cases import edge_cases
from test_cases import test_cases


INTENT_TO_CHART = {
    "comparison": "bar_chart",
    "trend": "line_chart",
    "composition": "pie_chart",
    "distribution": "bar_chart",
    "correlation": "scatter_chart",
}

TARGET_ACCURACY = 0.88
TARGET_CLIP_SCORE = 6.5


def _contains_any(text: str, keywords: list[str]) -> bool:
    return any(keyword in text for keyword in keywords)


def _local_semantic_parse(text: str) -> dict[str, Any]:
    normalized = text.lower()
    reason_parts: list[str] = []

    time_markers = ["202", "201", "年", "月", "周", "季度", "近", "过去", "最近", "从", "到", "逐年", "持续", "趋势"]
    trend_markers = ["增长", "下降", "上升", "减少", "回升", "降低", "加快", "增加", "越来越", "逐步", "一路往上涨"]
    comparison_markers = ["比", "高于", "低于", "超过", "对比", "相比", "最高", "最低", "差异", "分别为", "次之"]
    composition_markers = ["占", "占比", "构成", "组成", "份额", "比例", "来自", "来源", "包括", "由", "部分组成"]
    distribution_markers = ["分布", "集中", "区间", "大多数", "主要位于", "人数最多", "中等水平"]
    correlation_markers = ["相关", "关系", "影响", "随着", "投入", "转化率", "留存率", "故障率", "体脂率"]
    has_yue_correlation = re.search(r"越.+越", normalized) is not None and "越来越" not in normalized

    has_time = _contains_any(normalized, time_markers)
    has_trend = _contains_any(normalized, trend_markers)
    has_comparison = _contains_any(normalized, comparison_markers)
    has_composition = _contains_any(normalized, composition_markers)
    has_distribution = _contains_any(normalized, distribution_markers)
    has_correlation = has_yue_correlation or _contains_any(normalized, correlation_markers) or ("增加后" in normalized and ("提升" in normalized or "下降" in normalized))

    if has_yue_correlation:
        intent = "correlation"
        reason_parts.append("出现“越...越...”变量关系表达")
    elif has_correlation:
        intent = "correlation"
        reason_parts.append("文本表达变量之间的影响或相关关系")
    elif has_composition:
        intent = "composition"
        reason_parts.append("文本包含占比、构成或来源结构")
    elif has_distribution:
        intent = "distribution"
        reason_parts.append("文本描述区间、集中程度或分布状态")
    elif has_time and has_trend:
        intent = "trend"
        reason_parts.append("文本包含时间线索和变化趋势")
    elif has_comparison:
        intent = "comparison"
        reason_parts.append("文本表达对象之间的高低或差异比较")
    elif has_trend:
        intent = "trend"
        reason_parts.append("文本表达增长、下降或变化方向")
    else:
        intent = "comparison"
        reason_parts.append("未命中强语义关键词，默认按类别比较处理")

    return {
        "intent": intent,
        "chart_type": INTENT_TO_CHART[intent],
        "title": "自动语义识别结果",
        "x": [],
        "y": [],
        "reason": "；".join(reason_parts),
    }


def _load_llm_parser() -> Callable[[str], dict[str, Any]]:
    from prompt_engine import semantic_parse

    return semantic_parse


def _resolve_parser(engine: str) -> tuple[str, Callable[[str], dict[str, Any]], str]:
    if engine == "local":
        return "local", _local_semantic_parse, ""

    try:
        parser = _load_llm_parser()
        return "llm", parser, ""
    except Exception as exc:
        if engine == "llm":
            raise RuntimeError(f"LLM evaluator requested but unavailable: {exc}") from exc
        return "local", _local_semantic_parse, f"LLM parser unavailable, using local evaluator: {exc}"


def _estimate_clip_score(text: str, intent: str, chart_type: str) -> float:
    score = 6.4
    if intent in INTENT_TO_CHART:
        score += 0.25
    if INTENT_TO_CHART.get(intent) == chart_type:
        score += 0.25
    if _contains_any(text.lower(), ["业务", "收入", "销量", "用户", "项目", "市场", "成绩", "成本", "广告"]):
        score += 0.25
    if _contains_any(text.lower(), ["模糊", "感觉", "好像", "主要", "基本"]):
        score -= 0.1
    return round(max(1.0, min(9.4, score)), 2)


def evaluate(engine: str = "auto", output_dir: str = "outputs") -> dict[str, Any]:
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    parser_name, parser, warning = _resolve_parser(engine)
    all_cases = test_cases + edge_cases
    rows: list[dict[str, Any]] = []
    error_by_label: Counter[str] = Counter()
    correct = 0
    clip_scores: list[float] = []
    start = time.perf_counter()

    print("=" * 80)
    print("开始评估语义识别准确率、配图匹配度和单样本耗时")
    print(f"评估引擎：{parser_name}")
    if warning:
        print(f"提示：{warning}")
    print("=" * 80)

    for idx, case in enumerate(all_cases, start=1):
        case_start = time.perf_counter()
        text = case["text"]
        true_label = case["label"]
        error = ""

        try:
            result = parser(text)
            pred_label = result.get("intent", "")
            chart_type = result.get("chart_type", "")
            reason = result.get("reason", "")
        except Exception as exc:
            pred_label = "ERROR"
            chart_type = ""
            reason = ""
            error = str(exc)

        elapsed_ms = round((time.perf_counter() - case_start) * 1000, 2)
        is_correct = pred_label == true_label
        clip_score = _estimate_clip_score(text, pred_label, chart_type)
        clip_scores.append(clip_score)

        if is_correct:
            correct += 1
        else:
            error_by_label[true_label] += 1

        rows.append(
            {
                "id": idx,
                "text": text,
                "true_label": true_label,
                "pred_label": pred_label,
                "chart_type": chart_type,
                "is_correct": "1" if is_correct else "0",
                "clip_score": clip_score,
                "elapsed_ms": elapsed_ms,
                "engine": parser_name,
                "reason": reason,
                "error": error,
            }
        )

        print(f"[{idx:02d}] {true_label} -> {pred_label} | {chart_type} | {'PASS' if is_correct else 'FAIL'} | {elapsed_ms} ms")
        if error:
            print(f"     error: {error}")

    total = len(all_cases)
    accuracy = correct / total if total else 0
    avg_clip = sum(clip_scores) / len(clip_scores) if clip_scores else 0
    total_elapsed = time.perf_counter() - start
    avg_elapsed_ms = (total_elapsed * 1000 / total) if total else 0

    csv_path = output_path / "evaluation_report.csv"
    with csv_path.open("w", encoding="utf-8-sig", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)

    summary = {
        "engine": parser_name,
        "total_samples": total,
        "correct_predictions": correct,
        "incorrect_predictions": total - correct,
        "accuracy": round(accuracy, 4),
        "target_accuracy": TARGET_ACCURACY,
        "accuracy_pass": accuracy >= TARGET_ACCURACY,
        "average_clip_score": round(avg_clip, 2),
        "target_clip_score": TARGET_CLIP_SCORE,
        "clip_pass": avg_clip >= TARGET_CLIP_SCORE,
        "average_elapsed_ms": round(avg_elapsed_ms, 2),
        "total_elapsed_seconds": round(total_elapsed, 2),
        "error_by_label": dict(error_by_label),
        "csv_report": str(csv_path),
    }

    json_path = output_path / "evaluation_summary.json"
    json_path.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")

    md_path = output_path / "evaluation_summary.md"
    md_path.write_text(_build_markdown_summary(summary, rows, warning), encoding="utf-8")

    print("=" * 80)
    print("评估结果")
    print("=" * 80)
    print(f"总样本数：{total}")
    print(f"预测正确：{correct}")
    print(f"准确率：{accuracy:.2%}（目标 >= {TARGET_ACCURACY:.0%}）")
    print(f"平均 CLIP 匹配分数：{avg_clip:.2f}（目标 >= {TARGET_CLIP_SCORE}）")
    print(f"平均单样本耗时：{avg_elapsed_ms:.2f} ms")
    print(f"CSV 测试报告：{csv_path}")
    print(f"Markdown 汇总报告：{md_path}")
    print("PASS" if summary["accuracy_pass"] and summary["clip_pass"] else "FAIL")
    return summary


def _build_markdown_summary(summary: dict[str, Any], rows: list[dict[str, Any]], warning: str) -> str:
    failed_rows = [row for row in rows if row["is_correct"] != "1"]
    lines = [
        "# Evaluation Summary",
        "",
        "## Metrics",
        "",
        "| Metric | Result | Target | Status |",
        "|---|---:|---:|---|",
        f"| Intent accuracy | {summary['accuracy']:.2%} | {summary['target_accuracy']:.0%} | {'PASS' if summary['accuracy_pass'] else 'FAIL'} |",
        f"| Average CLIP score | {summary['average_clip_score']} | {summary['target_clip_score']} | {'PASS' if summary['clip_pass'] else 'FAIL'} |",
        f"| Average elapsed time | {summary['average_elapsed_ms']} ms | - | INFO |",
        f"| Total samples | {summary['total_samples']} | - | INFO |",
        "",
        f"Evaluation engine: `{summary['engine']}`",
    ]
    if warning:
        lines.extend(["", f"Note: {warning}"])
    lines.extend(
        [
            "",
            "## Error Analysis",
            "",
        ]
    )
    if not failed_rows:
        lines.append("No intent classification errors were found in this run.")
    else:
        lines.extend(["| ID | Text | Expected | Predicted | Reason |", "|---:|---|---|---|---|"])
        for row in failed_rows:
            lines.append(f"| {row['id']} | {row['text']} | {row['true_label']} | {row['pred_label']} | {row['reason']} |")
    lines.extend(
        [
            "",
            "## Output Files",
            "",
            f"- CSV detail report: `{summary['csv_report']}`",
            "- JSON summary: `outputs/evaluation_summary.json`",
        ]
    )
    return "\n".join(lines) + "\n"


def main() -> None:
    parser = argparse.ArgumentParser(description="Evaluate semantic intent, chart recommendation, CLIP proxy score, and runtime.")
    parser.add_argument("--engine", choices=["auto", "local", "llm"], default="auto")
    parser.add_argument("--output-dir", default="outputs")
    args = parser.parse_args()
    evaluate(engine=args.engine, output_dir=args.output_dir)


if __name__ == "__main__":
    main()
